import re
import time
from typing import Dict, List, Tuple, Union
import erppeek
import pandas as pd
from datetime import datetime

from application.packages.purchase import Purchase, Supplier
from application.packages.lobby import Lobby
from application.packages.utils import get_ceiling_date, update_item_auto_table_selector, get_delay

pd.options.mode.chained_assignment = None



class Odoo:
  def __init__(self):
    #STATUS
    self.builded = False
    self.connected = False

    #CONN
    self.client = None
    self.log = None
    self.tz = None
    self.user = None


  def connect(self, url, login, password, db, verbose):
    while self.connected == False:
      try:
        self.client = erppeek.Client(url, verbose=verbose)
        self.log = self.client.login(login, password=password, database=db)
        self.user = self.client.ResUsers.browse(self.log)
        self.tz = self.user.tz

        self.connected = True
      except Exception as e:
        print(e) #log latter
        time.sleep(60)


  def get(self, model: str, cond:List):
    result = self.client.model(model).get(cond)
    return result
  
  def browse(self, model:str, cond:List):
    result = self.client.model(model).browse(cond)
    return result

  def search_product_from_id(self, product_id):
    return self.client.model('product.product').get([('id', '=', product_id)])



  def search_product_from_ean(self, code_ean):
    """search for product object in product table."""
    return self.client.model('product.product').get([('barcode', '=', code_ean)])



  def search_alternative_ean(self, code_ean):
    """search in multi_barcode for scanned ean
    return product linked to main ean"""
    alt_product = self.client.model('product.multi.barcode').get([('barcode','=',code_ean)])
    if alt_product is not None:
      return self.client.model('product.multi.barcode').get([('barcode','=',code_ean)]).product_id

    else:
      return None


  def search_item_tmpl_id_from_product_id(self, product_id):
    return self.client.model('product.product').get([('id','=', product_id)]).product_tmpl_id.id


  def apply_purchase_record_change(self, move_id, received_qty):
    move = self.client.model('stock.move.line').get([('move_id.id','=', move_id)])
    move.qty_done = received_qty
    


  def get_picking_state(self, name):

    try:
      picking = self.client.model('stock.picking').get([('origin','=', name)])
      if picking:
        picking_state = picking.state

      else:
        picking_state = 'draft'

    except ValueError as e:
      # multiple picking ID heading towards a purchase.
      # most likely 1st is canceled and next one correct it.
      # state priority : None < Cancel < assigned < done
      picking = self.client.model('stock.picking').browse([('origin','=', name)])
      picking_state = None

      for pick in picking:
        if (pick.state == 'cancel' and 
          (picking_state != 'assigned' and picking_state != 'done')): # set up to cancel

          picking_state = pick.state

        elif pick.state == 'assigned' and picking_state != 'done': # set up to assigned
          picking_state = pick.state

        elif pick.state == 'done': # set up to done
          picking_state = pick.state

    return picking_state


  def get_item_state(self, name: str, id: int):

    try:
      item = self.client.model('stock.move').get([('origin','=', name), ('product_id.id','=', id)])
      if item:
        item_state = item.state

      else:
        item_state = 'none'

    except ValueError as e:
      # multiple picking ID heading towards a purchase.
      # most likely 1st is canceled and next one correct it.
      # state priority : None < Cancel < assigned < done
      items = self.client.model('stock.move').browse([('origin','=', name), ('product_id.id','=', id)])
      item_state = None

      for item in items:
        if (item.state == 'cancel' and 
          (item_state != 'assigned' and item_state != 'done')): # set up to cancel

          item_state = item.state

        elif item.state == 'assigned' and item_state != 'done': # set up to assigned
          item_state = item.state

        elif item.state == 'done': # set up to done
          item_state = item.state

    return item_state


  def get_purchase(self, timeDelta: list, data) -> None:
    """
    Collect tracked Odoo Purchases adn group them in sub-groups based on pruchase & picking state ['draft', 'incoming', 'received', 'done'].
    Purchase state : ['draft', 'purchase', 'cancel'], draft = price requeste, purchase = purchase incoming.
    picking state : ['assigned', 'done', 'cancel'], assigned = stock move awaiting to be verified, done = stock move verified


    Tracking pruchases:
    Inside timeDelta, newly added purchases between 2 update
    Previously classified as Draft. Following state evolution, either move the purchase to later stage or keep it as draft.
    Currently incoming / received purchases. Track purchase content, by searching for any modificaton/ cancellation on the parchase. Update it if necessary.

    @timeDelta : list [YEAR, MONTH, WEEK, DAY] as time difference between Now and targeted date.
    > time range for tracking purchases. Supplented by last get_purchase activation date if any.

    Global Variable:
    @data : dict

    Return Modification to nested dict data['odoo']['purchases'] and data['odoo']['history']['update_purchase']
    """

    draft = list(data['odoo']['purchases']['draft'].keys())
    incoming = list(data['odoo']['purchases']['incoming'].keys())
    received = list(data['odoo']['purchases']['received'].keys())
    done = list(data['odoo']['purchases']['done'].keys())

    date_ceiling = get_ceiling_date(timeDelta, data, 'update_purchase')
    
    purhasesList = (self.client.model('purchase.order').browse([('create_date', '>', date_ceiling)]) +
                   self.client.model('purchase.order').browse([('id', 'in', draft)]) + 
                   self.client.model('purchase.order').browse([('id', 'in', incoming)]) +
                   self.client.model('purchase.order').browse([('id', 'in', received)]))
    data['odoo']['purchases']['draft'] = {} # reset to avoid duplicate

    for pur in purhasesList:
      items = []

      id = pur.id
      name = pur.name
      supplier = pur.partner_id
      purchase_state = pur.state                                # ['draft','purchase','cancel']
      create_date = pur.create_date                             # date purchase is created in odoo
      added_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # date purchase is added in here

      if purchase_state == 'purchase' and id not in done: 
        print(name,'-', create_date)

        picking_state = self.get_picking_state(name) # ['assigned, cancel, done']
        
        if picking_state == 'cancel':
          # then remove the purchase
          Lobby().remove_room_associated_to_purchase(data, id)
          self.remove_purchase(data, id)

        elif picking_state == 'done':
          # then pass it to done dict adn remove it from previous dict
          exist = Lobby().update_room_associated_to_purchase(data, id, 'done')
          if exist:
            # room associated  exist, update purchase
            self.move_purchase(data, id, 'done')
            data['odoo']['purchases']['done'][id].change_status('received','verified')
            
          else:
            # room not exist, then no need to keep purchase
            self.remove_purchase(data, id)
          
        elif picking_state == 'assigned':
          if id not in incoming + received:
            # add purchase to dict
            moves = self.client.model('stock.move').browse([('origin', '=', name)])
            for item in moves:
              if item.state == 'assigned':   
                items.append([self.get_barcode(item), # item.product_id.barcode
                              item.product_id.id, 
                              re.sub('\[.*?\]', '', item.name).strip(), 
                              item.product_qty, 
                              item.product_qty_package, 
                              0])

            table = pd.DataFrame(items, columns=['barcode', 'id', 'name', 'qty', 'pckg_qty', 'qty_received'])
            data['odoo']['purchases']['incoming'][id] = Purchase(id, name, supplier, True, 'purchase', create_date, added_date, 'incoming', table)
          
          else:
            # in case modification has been made
            if id in incoming:
              purchase = data['odoo']['purchases']['incoming'][id]
              self.recharge_purchase(purchase, data)

            elif id in received:
              purchase = data['odoo']['purchases']['received'][id]
              self.recharge_purchase(purchase, data)

      elif purchase_state == 'draft':
        data['odoo']['purchases']['draft'][id] = None # Placeholder to keep tracking drafts
    
    data['odoo']['history']['update_purchase'].append(datetime.now().date().strftime("%Y-%m-%d %H:%M:%S"))

    return data


  def remove_purchase(self,data:Dict, id:int):
    if id in list(data['odoo']['purchases']['incoming'].keys()):
      data['odoo']['purchases']['incoming'].pop(id)
    
    elif id in list(data['odoo']['purchases']['received'].keys()):
      data['odoo']['purchases']['received'].pop(id)
      
    elif id in list(data['odoo']['purchases']['done'].keys()):
      data['odoo']['purchases']['done'].pop(id)
      

  def move_purchase(self, data:Dict, id:int, dest:str):
    if (id in list(data['odoo']['purchases']['incoming'].keys())
        and dest != 'incoming'):
      data['odoo']['purchases'][dest][id] = data['odoo']['purchases']['incoming'][id]
      data['odoo']['purchases']['incoming'].pop(id)
      
    elif (id in list(data['odoo']['purchases']['received'].keys())
          and dest != 'received'):
      data['odoo']['purchases'][dest][id] = data['odoo']['purchases']['received'][id]
      data['odoo']['purchases']['received'].pop(id) 

    elif (id in list(data['odoo']['purchases']['done'].keys())
          and dest != 'done'):
      data['odoo']['purchases'][dest][id] = data['odoo']['purchases']['done'][id]
      data['odoo']['purchases']['done'].pop(id)  


  def get_barcode(self, item) -> int:
    barcode = item.product_id.barcode
    alt = self.browse('product.multi.barcode', [('product_id','=',item.product_id.id)])

    if (barcode == False
        and alt):
      for p in alt:
        if p.barcode:
          barcode = p.barcode
          break
    return barcode
  
  
  def check_item_alt_integrity(self, item) -> Dict:

    item_barcode, item_id = item[0], item[1]
    main = self.get('product.product', [('id','=', item_id)])
    alts = self.browse('product.multi.barcode', [('barcode','=', item_barcode)])
    
    def check_alt():
      # verify if all ids are same
      # verify if all barcodes are the same

      if not main:
        check_i, check_b = alts[0].product_id.id, alts[0].barcode
      else:
        check_i, check_b = main.id, main.barcode
        
      for alt in alts:
        barcode = alt.barcode
        id = alt.product_id.id
        if check_i != id or check_b != barcode:
          return False
      return True


    if not item_barcode or not main:
      ## no product has barcode
      return {'item_validity': False, 'alt': None, 'has_main': False}
    
    elif not main.barcode and alts:
      # main product has no barcode, barcode is on alt
      # but multiple alts
      return {'item_validity': check_alt(), 'alt': alts[0], 'has_main': False}

    
    elif main.barcode and alts:
      return {'item_validity': check_alt(), 'alt': alts[0], 'has_main': True}

    else:
      # only main
      return {'item_validity': True, 'alt': None, 'has_main': True}

      
      

  def check_item_odoo_existence(self, table: pd.DataFrame) -> dict:
    item_list = []
    validity = True

    for item in table.values.tolist():
      print('__', item[0], '-', item[1] )
      result = self.check_item_alt_integrity(item)
      item_barcode = item[0]
      item_id = item[1]     
      
      item_validity = result['item_validity']
      print('valid__', item_validity)
      if item_validity:
        odoo_alt = result['alt']
        if not result['has_main']:
          odoo_barcode = odoo_alt.barcode
          odoo_id = odoo_alt.product_id.id
        else:
          odoo_barcode = self.get('product.product', [('id','=',item_id)]).barcode
          odoo_id = self.get('product.product', [('barcode','=',item_barcode)]).id
        
        if item_id != odoo_id or item_barcode != odoo_barcode:
          print('_',odoo_barcode, 'has a problem')
          item_validity = False
          validity = False
          item_list.append(item_barcode)
          continue
      
      else:
        # Odoo database problem where a product barcode refer to multiple products...
        print('odoo database duplicate problem...')
        print('__', item_barcode, '__')
        item_validity = False
        validity = False
        item_list.append(item_barcode)
        continue
      
    return {'validity': validity, 'item_list': item_list}


  def check_item_purchase_existence(self, purchase, table: pd.DataFrame, create: bool) -> dict:
    item_list = []
    validity = True
    id = purchase.id
    name = purchase.name

    for item in table[['barcode', 'id']].values.tolist():
      item_validity = True
      item_barcode = item[0]
      item_id = item[1]
      item_state = self.get_item_state(name, item_id)
      
      if item_state == 'none' and create:
        # Create purchase item in odoo
        print('init item creation')
        passed = self.create_purchase_record(purchase, item_id)
        if passed == False:
          item_list.append(name)
        
      elif item_state == 'none' and create == False:
        validity = False
        item_list.append(name)

    return {'validity': validity, 'item_list': item_list}




  def post_purchase(self, purchase, data, autoval) -> dict:

    purchase.process_status = 'verified'
    id = purchase.id
    name = purchase.name
    new_items = purchase.new_items
    table = purchase.table_done
    
    # ====> verify that the purchase is not already validated
    picking_state = self.get_picking_state(name)
    if picking_state == 'done':
      # already odoo validated, msg this information and block data transfer
      return {'validity': False, 'failed': 'validation_exist', 'item_list': ['']} 
    
    # ====> purchase_item exist in ODOO
    odoo_exist = self.check_item_odoo_existence(table)
    if odoo_exist['validity'] == False:
      # DATA VALIDITY IS TO BE PASSED TO ODOO
      return {'validity': False, 'failed': 'odoo_exist', 'item_list': odoo_exist['item_list']}
    print('test1 passed')

    # <==== room item all in odoo purchase
    purchase_exist = self.check_item_purchase_existence(purchase, table, data['config'].ODOO_CREATE_NEW_PURCHASE_LINE)
    if purchase_exist['validity'] == False:
      # All product from the app are not in the odoo purchase object.
      # purchase items can be create if odoo_create_new_purchase_item == True
      return {'validity': False, 'failed': 'purchase_exist', 'item_list': purchase_exist['item_list']}
    print('test2 passed')

    # APPLY MODIFICATION TO ODOO ITEMS
    moves = self.client.model('stock.move').browse([('origin', '=', name)])
    for move in moves:
      print('--', move.product_id)
      move_id = move.id
      move_state = move.state
      item_id = move.product_id.id

      if move_state == 'assigned' and purchase.is_received(item_id):
        received_qty = purchase.get_item_received_qty(item_id)
        self.apply_purchase_record_change(move_id, received_qty)
    
    return {'validity': True, 'failed': 'none', 'item_list': []}



  def product_supplier_data(self, purchase, product):
    partner_item = self.client.model('product.supplierinfo').get([('id','=', purchase.supplier.id),
                                                                   ('product_tmpl_id.id','=', product.product_tmpl_id.id)])
    if partner_item:
      price = partner_item.base_price
      product_code = partner_item.product_code

      if product_code:
        name = f'[{product_code}] {product.name}'

      else:
        name = product.name

    else:
      price = 1
      name = product.name

    return name, price


  def create_purchase_record(self, purchase, item_id):
    purchase_id = purchase.id

    product = self.search_product_from_id(item_id)
    if not product:
      # TEMPORARY TO PREVENT BAD ODOO MANIPULATION, IF ANY INATTENDED PROBLEMS
      # product does not exist on Odoo
      # This very case might not happen as we check already product existence in odoo
      return False

    uom = product.product_tmpl_id.uom_id.id
    name, price = self.product_supplier_data(purchase, product)

    new_item = {'order_id': purchase_id,
                'product_uom': uom,
                'price_unit': price,
                'product_qty': 1, #0
                'name': name,
                'product_id': product,
                'date_planned': datetime.now()}

    self.client.model('purchase.order.line').create(new_item)

    return True


  def recharge_purchase(self, purchase, data) -> None:
    """Request to update purchase data from odoo
    keep room table structure untouched
    In use when odoo is modified eg: 
    new product added in odoo, 
    change in quantity, pkg qty, name, barcode
    product supr
    ...
    return purchase object 
    """

    id = purchase.id
    name = purchase.name
    purchase_state = self.client.model('purchase.order').get([('id', '=', id)]).state
    picking_state = self.get_picking_state(name) 
    if purchase_state == 'purchase' and picking_state == 'assigned':
      moves = self.client.model('stock.move').browse([('origin', '=', name)])
      passed = False

      for item in moves:
        # if item.state == 'assigned':   
        productData = {'item_id': item.product_id.id,
                      'item_barcode': self.get_barcode(item), #item.product_id.barcode
                      'item_name': re.sub('\[.*?\]', '', item.name).strip(),
                      'item_qty': item.product_qty,
                      'item_qty_packaqe': item.product_qty_package,
                      'item_qty_received': 0}
        update_item_auto_table_selector(purchase, productData, purchase.process_status, item.state)
      
    elif purchase_state == 'cancel' or picking_state == 'cancel':
      # remove from data dict
      if id in list(data['odoo']['purchases']['incoming'].keys()):
        data['odoo']['purchases']['incoming'].pop(id)

      elif id in list(data['odoo']['purchases']['received'].keys()):
        data['odoo']['purchases']['received'].pop(id)
    

  def delete_purchase(self, id, data, object_type, state):
    if state == 'done':
      if object_type == 'purchase':
        data['odoo']['purchases']['done'].pop(id)
      else:
        data['odoo']['inventory']['done'].pop(id)
        
    elif state == 'received':
      if object_type == 'purchase':
        data['odoo']['purchases']['received'].pop(id)
      else:
        data['odoo']['inventory']['processed'].pop(id)
  
  
  def get_product_categories(self, data:Dict) -> List[Tuple[str, int]]:
    """Generate list of product categories existing in odoo. sort it by lexicographic order
    
    place the data into the data dict: data['odoo']['inventory']['type']

    Returns:
        List[Tuple[str, int]]: list of tuple name and id of product categories.
    """

    categories = self.browse('product.category', [(['create_date','>','1900-01-01 01:01:01'])]) # api does not work without conditions
    cat = sorted([(c.complete_name, c.id) for c in categories],                                 # setup obvious cond. as turn around
                  key=lambda x: x[0],
                  reverse=False)
    
    data['odoo']['inventory']['type'] = cat
    
    return data   


  ################ INVENTORY #########################
  def generate_inv_product_table(self, cat_id:int) -> pd.DataFrame:
    """takes a category id as input, generate list of product records from this categ
        products records are : pp id, pt name, pp or pmb barcode, pt stock qty

    Args:
        cat_id (int): reference to a category

    Returns:
        List: list of all products records with input cat id.
    """
    
    def get_barcode() -> Union[str,bool]:
      barcode = pp.barcode   
      if (not barcode and pmb):
        for p in pmb:
          if p.barcode:
            barcode = p.barcode
            break 

      return barcode
    
    def get_name_translation() -> str:
      name = None
      for t in irt:
        if t.name == 'product.template,name':
          name = t.value
          break
      
      if not name:
        name = pt.name

      return name
    
    # name, barcode or multiple barcode, theoric qty, real quantity
    product_list = []
    products = self.browse('product.template', [('categ_id', '=', cat_id),
                                                ('active', '=', True)])
    for pt in products:
      tmpl_id = pt.id
      irt = self.browse('ir.translation', [('res_id','=', tmpl_id)])
      pp = self.get('product.product', [(['product_tmpl_id', '=', tmpl_id])])
      pmb = self.browse('product.multi.barcode', [(['product_id','=', pp.id])])    
      name = get_name_translation()
      
      qty = pt.qty_available
      virtual = pt.virtual_available
                      
      id = pp.id
      barcode = get_barcode()

      product_list.append([barcode, id, name, qty, virtual, qty])  
    
    return pd.DataFrame(product_list, columns=['barcode', 'id', 'name', 'qty', 'virtual_qty', 'qty_received'])



  def create_inventory(self, input:Dict, data: Dict, table: pd.DataFrame) -> int:
    #generate Purchase object for inventory
    def get_id() -> int:
      ongoing = list(data['odoo']['inventory']['ongoing'].keys())
      done = list(data['odoo']['inventory']['done'].keys())
      m = max(ongoing + done, default=0)
      return m + 1     
    
    inv_id = get_id()
    cat_id = input['object_id']
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inventory = Purchase(inv_id,
                         [x[0] for x in data['odoo']['inventory']['type'] if x[1] == cat_id][0],
                         Supplier(None, 'inventaire'),
                         True,
                         'inventory',
                         now,
                         now,
                         'incoming',
                         table)
    print(cat_id)
    print(inventory, inventory.id, inventory.name)
    data['odoo']['inventory']['ongoing'][inv_id] = inventory
    return inv_id
 


  def post_inventory(self, inventory:Purchase, data:Dict, autoval:bool) -> bool:
    """_summary_

    Args:
        inventory (Purchase): purchase object containing related inventory data
        data (Dict): global data dict 

    Returns:
        bool: _description_
    """
    
    ## CREATE A STOCK.INVENTORY ROW
    ## CREATE STOCK.INVENTORY.LINE FOR THE CREATED INVENTORY
    ### WITH CHECK ON ODOO PRODUCT EXISTENCE
    ### WITH INVENTORED QTY

    ## SHOULD ALLLOW AUTO VALIDATION PROCESS..
    print('in post inventory')
    odoo_exist = self.check_item_odoo_existence(inventory.table_done)
    if odoo_exist['validity'] == False:
      # DATA VALIDITY IS TO BE PASSED TO ODOO
      return {'validity': False, 'failed': 'odoo_exist', 'item_list': odoo_exist['item_list']}
    
    print('test1 passed')
    c = self.create_stock_inventory_row(inventory)
    c = self.create_stock_inventory_line_row(inventory, c)
    c = self.propagate_start(c)
    self.propagate_validate(c, autoval)
    
    return {'validity': True, 'failed': 'none', 'item_list': []}



  def create_stock_inventory_row(self,inventory:Purchase):
    date = datetime.now().strftime("%d-%m-%Y")
    name = f'{inventory.name} {date}'
    
    return self.client.model('stock.inventory').create(
                                                      {'name': name,
                                                      'filter': 'categories',
                                                      'location_id': 12
                                                      })



  def create_stock_inventory_line_row(self, inventory:Purchase, container):
    _,_,records = inventory.get_table_records()
    for r in records:
      product = self.client.model('product.product').get([('id', '=', r['id'])])
      uom = product.product_tmpl_id.uom_id.id
      
      self.client.model('stock.inventory.line').create(
        {
          'product_qty': r['qty_received'],
          'product_id': r['id'],
          'product_uom_id': uom,
          'location_id': 12,
          'inventory_id': container.id,
        })
    
    return container

  def propagate_start(self, container):
    container.action_start()
    return container

  def propagate_validate(self, container, autoval:bool):
    if autoval:
      try:
        container.action_validate()
      except Exception:
        # catch marshall error & pass it
        pass





  #################### BUILD ##############################
  def build(self, data, url, login, password, db, verbose, timeDelta):
    """Building base dataset
    activate only on first activation of the server"""
    self.connect(url, login, password, db, verbose)
    data = self.get_purchase(timeDelta, data)
    data = self.get_product_categories(data)

    self.builded = True

    return data
