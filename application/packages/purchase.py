import pandas as pd
from typing import Union, Tuple, Type, List

class Supplier:
  """supplier data to hold odoo supplier informations
  avoid to hold odoo xml data
  @id: id
  @name: is partner id
  """
  def __init__(self, partner_id, partner_name):
    self.id = partner_id
    self.name = partner_name
    

class Purchase:
  """
  PURCHASE INSTANCE or INVENTORY INSTANCE
  often just use 'OBJECT' as this class represent inventories despite the name.
   
  Purchase object is the representation of all odoo purchases or inventories sessions
  It contains its product data and any related (and useful) data such as states and datetimes.
  
  IDENTIFIERS:
  @id (int): UNIQUE id for the object. ID used to store object inside cache as follow
             cache['odoo']['purchase'][status][id]
             cache['odoo']['inventory'][status][id]
  @name (str): name collected from odoo, based on id such as 'PO'+id for purchases
  @supplier (class: Supplier): supplier data collected from odoo, placeholder when no informations
  
  TABLES:
  @table (pd.Dataframe): is origin state of the Object products data
  @table_entries (pd.Dataframe): Processing table containing untouched products
  @table_queue (pd.Dataframe): Processing talbe containing scanned, but unmodified products
  @table_done (pd.Dataframe): Processing table containing modified items
  
  LISTS:
  all list contains manipulated product barcodes (int)
  all are incremented while scanning items
  @wrong_items (List[int]): UNUSED
  @scanned_barcodes (List[int]): avoid rescanning items
  @new_items (List[int]): label products that are not originally in the object, help indicating (coloring) items in display
  @modified_items (List[int]): label products that received any modification compared to their original states
  
  STATES:
  @realness (bool): whether the object is based on a true odoo object (purchase or inventory), or an abstract one.
                    abstract one are mainly named "speudo-purchase", can only be a purchase when abstract
  @ptype (str): can be ['inventory', 'purchase'], intern label to indicate and modify object regarding its purpose
  @status (str): can be ['incoming', 'received'] for purchases
                 can be ['ongoing', 'processed'] for inventory
                 label if the object has arrived yet, its type is related to cache category
                 cache['odoo']['purchase'][status] or
                 cache['odoo']['inventory'][status]
  @process_status (str): can be [None ,started, finished, verified], label the reception process
                        'None' when no linked room have been created, no process started yet
                        'Started' when a linked room is created
                        'finished' when reception is done and object is to be verified by administrators
                        'done' when whole process is finished ( object has been verified and sent to odoo)
                        
  DATETIMES:
  @create_date (str): is odoo create_time attribute
  @added_date (str): is datetime when object is created in the application
  """
  
  def __init__(self, id, name, supplier, realness, ptype, create_date, added_date, status, table):
    self.id = id
    self.name = name
    
    if supplier is None:
      self.supplier = Supplier(None, 
                               None)
    else:
      self.supplier = Supplier(supplier.id, 
                               supplier.name)

    self.supplier_name = self.get_supplier_name()
    self.real = realness
    self.pType = ptype
    self.create_date = create_date
    self.added_date = added_date
    self.status = status
    self.table = table

    self.wrong_items = [] 
    self.scanned_barcodes = []
    self.new_items = []
    self.modified_items = []
    self.process_status = None
    
    self.table_entries = None
    self.table_queue = None
    self.table_done = None


  def get_supplier_name(self):
    """handle supplier placeholder
    when this attribute is requested to be display"""
    if self.supplier:
      name = self.supplier.name
    
    else:
      name = 'none'

    return name


  def status_quo(self):
    """transfert purchased qty value to received qty as initial status quo value."""

    self.table_entries['qty_received'] = self.table_entries['qty']


  def build_process_tables(self):
    """build purchase starting position or reset position"""

    self.scanned_barcodes = []
    self.new_items = []
    self.modified_items = []
    self.table_entries = self.table
    self.table_queue = pd.DataFrame([], columns= list(self.table.columns))
    self.table_done = pd.DataFrame([], columns= list(self.table.columns))

    self.status_quo()
    self.process_status = 'started'


  def get_table_records(self):
    """extract Dataframe data as dict records

    Returns:
        _type_: tuple of series of dict
    """
    entry_records = self.table_entries.to_dict('records')
    queue_records = self.table_queue.to_dict('records')
    done_records = self.table_done.to_dict('records')

    return entry_records, queue_records, done_records
  

  def active_tables(self) -> List[str]:
    """return list of currently active tables"""
    return [tb for tb in ['table_entries', 'table_queue', 'table_done'] 
            if getattr(self, tb) is not None]
    

  def is_received(self, id):
    table = self.table_done
    return table[table['id'] == id]['id'].any()



  def get_item_received_qty(self, id):
    table = self.table_done
    received_qty = table[table['id'] == id]['qty_received'].values.tolist()[0]

    return received_qty

  def append_new_items(self, barcode):
    if barcode not in self.new_items:
      self.new_items.append(barcode)


  def append_modified_items(self, barcode):
    if barcode not in self.modified_items:
      self.modified_items.append(barcode)


  def append_scanned_items(self, barcode):
    if barcode not in self.scanned_barcodes:
      self.scanned_barcodes.append(barcode) 

  def get_item_origin_index(self, product:dict) -> Union[None,int]:
    """search the requested product inside origin table

    Args:
        product (dict): product related data dict

    Returns:
        Union[None, int]: product row index if any
    """
    origin_idx = None
    p = self.table.loc[(self.table["barcode"] == product['barcode']) | (self.table["id"] == product['id'])]
    if not p.empty: origin_idx = p.index.tolist()[0]
    
    return origin_idx
  
  def get_item_location_index(self, product: dict) -> Tuple[Union[None, int], Union[None, str]]:
    """search the requested product inside all sub tables.

    Args:
        product (dict): product related data dict

    Returns:
        Tuple[Union[None, int], Union[None, str]]: product row index if any, table name if any
    """
    
    idx, loc = None, None
    for tbname in self.active_tables():
      table = getattr(self, tbname)
      p = table.loc[(table["barcode"] == product['barcode']) | (table["id"] == product['id'])]
      if not p.empty:
        idx = p.index.tolist()[0]
        loc = tbname
        break
      
    return idx, loc

  def update_item(self, table_name:str, idx:int, product:dict) -> None:
    """update a product row to the selected table

    Args:
        table_name (str): name of the purchase table to update
        idx (int): idx of the row to update
        product (dict): product related data dict
    """
    table = getattr(self, table_name)
    table.loc[idx, ['barcode','name','qty','pckg_qty']] = [product['barcode'],
                                                           product['name'],
                                                           product['qty'],
                                                           product['qty_packaqe']] 
    setattr(self, table_name, table)
  
  def remmove_from_scanned(self, barcodes: List[int]) -> None:
    """remove item from scanned items list"""
    for idx in barcodes:
      try:
        loc = self.scanned_barcodes.index(idx)
        self.scanned_barcodes.pop(loc)
      except ValueError:
        """not in list"""
        pass
 
  def delete_item(self, table_name:str, idx:int) -> None:
    """delete a product row to the selected table

    Args:
        table_name (str): name of the purchase table to update
        idx (int): idx of the row to delete
    """
    table = getattr(self, table_name)
    rm_scanned = table.loc[idx, 'barcode'].values.tolist()
    self.remmove_from_scanned(rm_scanned)    
    table = table.drop(idx, axis=0)
    table = table.reset_index(drop=True)
    setattr(self, table_name, table)



  def create_item(self, table_name:str, product:dict) -> None:
    """add a product row to the selected table

    Args:
        table_name (str): name of the purchase table to update
        product (dict): product related data dict
    """
    table = getattr(self, table_name)
    row = pd.DataFrame([[product['barcode'], 
                        product['id'], 
                        product['name'], 
                        product['qty'], 
                        product['qty_packaqe'], 
                        product['qty_received']]],
       columns= table.columns.tolist())

    table = pd.concat([table, row], ignore_index=True)
    setattr(self, table_name, table)


  def recharge_item(self,
            product: dict,
            state: Union[None, str],
            item_state: str) -> None:
    """main process for updating item
    search item in purchase table and chose
    between deleting, updating or creating the product

    Args:
        product (dict): product related data dict
        state (Union[None, str]): state of the purchase, None when never linked to room
        item_state (str): item state fetched from odoo
    """

    ## SEARCH ITEM
    origin_idx = self.get_item_origin_index(product)
    idx, loc = self.get_item_location_index(product)

    ### item to be found with barcode or id if no barcode
    ## APPLY UPDATE RELATED TO ITS STATUS
    if item_state == 'cancel':
      # DELETE ROW
      if origin_idx != None:
        self.delete_item('table', origin_idx)
      if idx != None:
        self.delete_item(loc, idx)

    elif item_state != 'cancel' and state:
      if origin_idx == None and self.process_status == None:
        ## CREATE ROW IN TABLE AND LOC
        self.create_item('table', product)
        
      elif origin_idx == None and self.process_status != None:
        self.create_item('table', product)
        self.create_item('table_entries', product)
      
      elif origin_idx and not idx:
        ## UPDATE ROW IN origin and loc
        self.update_item('table', origin_idx, product)
        
      elif origin_idx and idx:
        self.update_item('table', origin_idx, product)
        self.update_item(loc, idx, product)


  def update_table_on_edit(self, context:dict) -> dict:
    """APPLY ANY TABLE TRANSACTION AND MODIFICATION

    Args:
        context (dict): contain the context of the transaction

    Returns:
        dict: context of the transaction to be broadcasted to all active clients
    """
    self.append_scanned_items(context['barcode'])

    table = getattr(self, context['table'])
    product = table[(table['barcode'] == context['barcode']) |
                    (table['id'] == int(context['product_id']))]
    
    if context['type'] == 'mod': 
      # APPLY MODIFICATION TO RECEIVED QTY WHEN CONTEXT SPECIFY A MODIFICATION
      product.loc[product.index, 'qty_received'] = context['newqty']
      self.append_modified_items(context['barcode'])
    
    if context['table'] != "table_done":
      # RECQUIRE TO DROP PRODUCT FROM PREVIOUS TABLE AND
      # CONCAT IT TO DONE TABLE
      table = table.drop(product.index, axis=0)
      table = table.reset_index(drop=True)
      setattr(self, context['table'], table)
      setattr(self, "table_done", 
              pd.concat([self.table_done, product], ignore_index=True))
      
    else:
      # SIMPLY APPLY QUANTITY MODIFICATION
      self.table_done.loc[product.index, 'qty_received'] = context['newqty']  
    
    context['scanned'] = self.scanned_barcodes
    context['new'] = self.new_items
    context['mod'] = self.modified_items
    return context




  ####################################################################
  ########################### SEARCH SCANNED ITEM ####################
  def _get_product_out_of_exceptions(self, odoo: object, model:str, context: dict) -> dict:
    products = odoo.browse(model, [('barcode', '=', context['code_ean'])])
    product = products[0]
    for pr in products: 
      if ((model == "product.product" and
          context['code_ean'] == pr.barcode) or
          (model == "product.multi.barcode" and
           context['code_ean'] == pr.barcode and
           context['code_ean'] == pr.product_id.barcode)):
        product= pr
        break
    
    return product 

  def _state_0_search(self, context:dict) -> dict:
    """search item inside table entrie.
    if item is found break search process
    state remain 0
    
    Args:
        context (dict): current item context

    Returns:
        dict: current item context
    """
    context['product'] = self.table_entries[
      (self.table_entries['barcode'] == context['code_ean'])
      ]

    if context['product'].empty:
      context['state'] = 1
      
    else:
      context['flag'] = False

    return context
    
  def _state_1_search(self, odoo: object, context: dict) -> dict:
    """search item into product.multi.barcode table.
    if item is found break search process
    state fixed to 1 if the found item is also inside table entries
    state fixed to 2 if the item is not inside table entries
    state fixed to 2 if item not found into table entries, flag not turned off
    
    Args:
        odoo (Odoo): odoo object to build odoo queries
        context (dict): current item context

    Returns:
        dict: current item context
    """
    try:
      alt = odoo.get('product.multi.barcode', 
                     [('barcode','=',context['code_ean'])])

    except ValueError:
      # just select first one in this case
      alt = self._get_product_out_of_exceptions(odoo,
                                                "product.multi.barcode", 
                                                context)
    if not alt:
      context['state'] = 2
    
    elif self.table_entries[(self.table_entries['barcode'] == alt.barcode)].empty:
      ## GET PRODUCT DATA FROM ODOO
      context['product'] = alt.product_id
      context['state'] = 2
      context['flag'] = False
      
    else:
      context['product'] = self.table_entries[(self.table_entries['barcode'] == alt.barcode)]
      context['flag'] = False

    return context
  

      
  
  def _state_2_search(self, odoo: object, context: dict) -> dict:
    """search item into product.product table.
    if item found into odoo fix state to 2
    state up to 3 otherwise. 
    break process 
    
    Args:
        odoo (Odoo): odoo object to build odoo queries
        context (dict): current item context

    Returns:
        dict: current item context
    """
    try:
      # barcode is supposed unique, but it appear that several items can be pulled out 
      # while requesting a barcode.
      ## abnormal behavior arise when a product is copyed inside the database.
      ## even if you change the barcode, original barcode keep its print, even though it is nowhere to be found.
      context['product'] = odoo.get('product.product', 
                                    [('barcode', '=', context['code_ean'])])

    except ValueError:
      # WHEN MULTIPLE APPEARANCE IS FOUND
      # TRY TO SELECT PRODUCT WITH MAIN BARCODE 
      context['product'] = self._get_product_out_of_exceptions(odoo,
                                                               'product.product', 
                                                               context)
      
    if context['product']:
      context['flag'] = False
    else:
      context['state'] = 3
      context['product'] = None
      context['flag'] = False
        
    return context
 
  def _move_scanned_item(self, context: dict) -> dict:
    """take an item and place it into the queue table
    -item can be in table entries, thus it is moved into next table
    -item can be odoo thus being imported into the purchase object
    - item nowhere to be found, imported with minimal known informations

    Args:
        context (dict): context about product localisation

    Returns:
        dict: product data to be broadcasted
    """
    if context['state'] in [0,1]:
      ## MOVE FROM ENTRIES TO QUEUES
      new_item = False
      self.table_queue = pd.concat([self.table_queue, context['product']], 
                                            ignore_index=True)
      self.table_entries = self.table_entries.drop(context['product'].index, 
                                                                     axis=0)
      self.table_entries = self.table_entries.reset_index(drop=True)
      
      product_data = context['product'].values.tolist()[0][1:]
      id, name, qty, pkg_qty, received_qty = product_data
      
    elif context['state'] in [2,3]:
      new_item = True
      qty, pkg_qty, received_qty = 0, 0, 0
      self.append_new_items(context['code_ean'])
      if context['state'] == 2:
        # found in either product multi or product
        name = context['product'].name
        id = context['product'].id

      elif context['state'] == 3:
        # not in purchase object nor in odoo
        id, name = 0, ''

      columns = self.table_queue.columns.tolist()
      placeholder = pd.DataFrame([[context['code_ean'],
                                   id, 
                                   name, 
                                   qty, 
                                   pkg_qty, 
                                   received_qty]]
                          , columns= columns)
      placeholder.fillna(0, inplace=True)
      self.table_queue = pd.concat([self.table_queue, placeholder], ignore_index=True)
      
    #broadcasting update
    return {'barcode': context['code_ean'],
            'id': id,
            'name': name,
            'qty':  qty,
            'pckg_qty': pkg_qty,
            'qty_received': received_qty,
            'new_item': new_item} 

  ####################################################################
  ########################### END SEARCH SCANNED ITEM ################




  def change_status(self, status:str, process_status:str):
    self.status = status
    self.process_status = process_status
    

  def assembler(self, other: object):
    """INVENTORY RELATED FUNCTION
    merge 2 inventory object together
    finally supress the other inventory instance

    Args:
        other (Type[Purchase]): Another Purchase instance
    """
    
    def merge_list():
      self.wrong_items = list(set(self.wrong_items + other.wrong_items))
      self.scanned_barcodes = list(set(self.scanned_barcodes + other.scanned_barcodes))
      self.new_items = list(set(self.new_items + other.new_items))
      self.modified_items = list(set(self.modified_items + other.modified_items))
    
    def merge_qty():
      v = self.table_done.loc[self.table_done['id'] == record['id'], 'qty_received']
      self.table_done.loc[self.table_done['id'] == record['id'], 'qty_received'] = int(v) + int(record['qty_received'])
    
    def drop_duplicate_row():
      if self.table_entries.loc[self.table_entries['id'] == record['id'], 'qty_received'].any():
        self.table_entries = self.table_entries.drop(self.table_entries.loc[self.table_entries['id'] == record['id'], 'qty_received'].index)
        
      if self.table_queue.loc[self.table_queue['id'] == record['id'], 'qty_received'].any():
        self.table_queue = self.table_queue.drop(self.table_queue.loc[self.table_queue['id'] == record['id'], 'qty_received'].index)
    
    def concat_new_row():
      row = pd.DataFrame([[record['barcode'], 
                            record['id'], 
                            record['name'], 
                            record['qty'], 
                            record['virtual_qty'], 
                            record['qty_received']]], 
                          columns=['barcode', 'id', 'name', 'qty', 'virtual_qty', 'qty_received'])
      self.table_done = pd.concat([self.table_done, row])
      
      
    ##########main
    oth_tb_done = other.table_done.to_dict('records')
    for record in oth_tb_done:
      if self.table_done.loc[self.table_done['id'] == record['id'], 'qty_received'].any():
        merge_qty()
      else:
        drop_duplicate_row()
        concat_new_row()

    self.table_done = self.table_done.reset_index(drop=True)
    merge_list()
    
    
  def nullifier(self):
    """INVENTORY RELATED FUNCTION
    takes product from queue and entries tables 
    set there qty_received to 0 and move the product into done table
    """
    self.modified_items.extend(self.table_entries['barcode'].values.tolist())
    self.modified_items.extend(self.table_queue['barcode'].values.tolist())
    
    self.table_entries = self.table_entries.assign(qty_received=0)
    self.table_queue = self.table_queue.assign(qty_received=0)
    
    self.table_done = pd.concat([self.table_done, self.table_queue, self.table_entries])
    self.table_done = self.table_done.reset_index(drop=True)
    self.table_entries = pd.DataFrame(columns=['barcode', 'id', 'name', 'qty', 'virtual_qty', 'qty_received'])
    self.table_queue = pd.DataFrame(columns=['barcode', 'id', 'name', 'qty', 'virtual_qty', 'qty_received'])


    


    