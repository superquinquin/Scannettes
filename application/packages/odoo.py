import re
import time
from typing import Dict, List, Tuple, Union
import erppeek
import pandas as pd
from datetime import datetime

from application.packages.purchase import Purchase, Supplier
from application.packages.lobby import Lobby
from application.packages.utils import get_ceiling_date, format_error_cases

pd.options.mode.chained_assignment = None



class Odoo:
  """ODOO INSTANCE
  communicate with odoo database
  
  STATUS
  @builded (bool): True when cache is builded during build function
  @connected (bool): wether the instance is connected to odoo database
                     when False, try to reconnect every 60s
  
  ERPPEEK API ATTR
  @client: odoo erppeek client instance
  @log: erppeek log
  @tz: erppeek tz
  @user: erppeek user.
  """
  
  
  def __init__(self):
    #STATUS
    self.builded = False
    self.connected = False

    #CONN
    self.client = None
    self.log = None
    self.tz = None
    self.user = None


  def connect(self, url: str, login: str, password: str, db: str, verbose: bool):
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


  def get(self, model: str, cond:List[Tuple[str]]):
    """short for odoo client get method"""
    result = self.client.model(model).get(cond)
    return result
  
  def browse(self, model:str, cond:List[Tuple[str]]):
    """short for odoo client browse method"""
    result = self.client.model(model).browse(cond)
    return result
  
  def create(self, model:str, object:dict):
    """short for odoo client create method"""
    result = self.client.model(model).create(object)
    return result

  def apply_purchase_record_change(self, move_id: int, received_qty: int):
    """during post purchase process update odoo record value"""
    move = self.get('stock.move.line', [('move_id.id','=', move_id)])
    move.qty_done = received_qty
    
  def get_barcode(self, item) -> int:
    """ get barcode from multibarcode table
    handle False barcode from odoo"""
    barcode = item.product_id.barcode
    alt = self.browse('product.multi.barcode', [('product_id','=',item.product_id.id)])

    if (barcode == False
        and alt):
      for p in alt:
        if p.barcode:
          barcode = p.barcode
          break
    return barcode

  def get_name_translation(self, product) -> str:
    """search product template id in translation table
    IF ANY translation select it as name
    OTHERWISE keep product template name

    Args:
        tmpl_id (int): product.template id 

    Returns:
        str: last updated product name
    """
    name = None
    irt = self.browse('ir.translation', 
                      [('res_id','=', product.product_tmpl_id.id)])
    for t in irt:
      if t.name == 'product.template,name':
        name = t.value
        break
    if not name:
      name = product.name
    return name


  def get_picking_state(self, name: str) -> str:
    """try to search picking state of a purchase
    
    ON VALUE ERROR due to multiple picking id 
    certainly from reediting purchase and cancel previous ones
    give priority as follow:
    None < Cancel < assigned < done
    
    Args:
        name (str): origin field in stock picking field

    Returns:
        str: current picking state, can be [None, 'cancel','assigned','done']
    """
    try:
      picking = self.get('stock.picking', [('origin','=', name)])

      if picking:
        picking_state = picking.state

      else:
        picking_state = 'draft'

    except ValueError as e:
      picking = self.browse('stock.picking', [('origin','=', name)])
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


  def get_item_state(self, name: str, id: int) -> str:
    """try to search for item state
    
    ON VALUE ERROR 
    can be due to multiple item with same id,
    originating from canceled item and reediting ones
    state priority : None < Cancel < assigned < done
    
    Args:
        name (str): origin field from stock.move
        id (int): product id

    Returns:
        str: item state, can be [None, 'cancel','assigned','done']
    """
    try:
      item = self.get('stock.move', [('origin','=', name), 
                              ('product_id.id','=', id)])
      if item:
        item_state = item.state

      else:
        item_state = 'none'

    except ValueError as e:

      items = self.browse('stock.move', [('origin','=', name), 
                                        ('product_id.id','=', id)])
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


  def get_purchase(self, timeDelta: list, data: dict) -> dict:
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
    @data: cache data dict

    Return Modification to nested dict data['odoo']['purchases'] and data['odoo']['history']['update_purchase']
    """
    draft = list(data['odoo']['purchases']['draft'].keys())
    incoming = list(data['odoo']['purchases']['incoming'].keys())
    received = list(data['odoo']['purchases']['received'].keys())
    done = list(data['odoo']['purchases']['done'].keys())
    date_ceiling = get_ceiling_date(timeDelta, data, 'update_purchase')
    purchasesList = (
      self.browse('purchase.order', [('create_date', '>', date_ceiling)]) +
      self.browse('purchase.order', [('id', 'in', draft)]) +
      self.browse('purchase.order', [('id', 'in', incoming)]) +
      self.browse('purchase.order', [('id', 'in', received)])  
    )
    data['odoo']['purchases']['draft'] = {} # reset to avoid duplicate

    for pur in purchasesList:
      # pur.states ['draft','purchase','cancel']
      id, name, purchase_state, create_date = pur.id, pur.name, pur.state, pur.create_date
                            
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
            self.add_purchase(pur, name, id, data)
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

  def add_purchase(self, pur, name:str, id:str, data: dict):
    """add purchase into the cache"""
    items = []
    supplier = pur.partner_id
    create_date = pur.create_date                             
    added_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    moves = self.browse('stock.move', [('origin', '=', name)])
    for item in moves:
      if item.state == 'assigned':   
        items.append([self.get_barcode(item), # item.product_id.barcode
                      item.product_id.id, 
                      re.sub('\[.*?\]', '', self.get_name_translation(item.product_id)).strip(),
                      item.product_qty, 
                      item.product_qty_package, 
                      0])

    table = pd.DataFrame(items, 
                         columns=['barcode', 'id', 'name', 'qty', 'pckg_qty', 'qty_received'])
    data['odoo']['purchases']['incoming'][id] = Purchase(id, 
                                                         name, 
                                                         supplier, 
                                                         True, 
                                                         'purchase', 
                                                         create_date, 
                                                         added_date, 
                                                         'incoming', 
                                                         table)
    

  def remove_purchase(self,data:Dict, id:int):
    """ handle remove a purchase during get_purchase method"""

    if id in list(data['odoo']['purchases']['incoming'].keys()):
      data['odoo']['purchases']['incoming'].pop(id)
    
    elif id in list(data['odoo']['purchases']['received'].keys()):
      data['odoo']['purchases']['received'].pop(id)
      
    elif id in list(data['odoo']['purchases']['done'].keys()):
      data['odoo']['purchases']['done'].pop(id)
      

  def move_purchase(self, data:Dict, id:int, dest:str):
    """handle move purchase during get_purchase method"""
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



  
  
  def check_item_alt_integrity(self, item) -> Dict:
    """request odoo for main and mulitbarcode products
    WHEN ALTS, CHECKS ALT ID AND BARCODE CONSISTENCIES
    
    RETURN ITEM VALIDITY CHECK
    """
    item_barcode, item_id = item[0], item[1]
    main = self.get('product.product', [('id','=', item_id)])
    alts = self.browse('product.multi.barcode', [('barcode','=', item_barcode)])
    
    def check_alt():
      # verify if all ids are same
      # verify if all barcodes are the same
      try:
        if not main:
          check_i, check_b = alts[0].product_id.id, alts[0].product_id.barcode
        else:
          check_i, check_b = main.id, main.barcode
      except IndexError:
        return False
      
      for alt in alts:
        barcode = alt.product_id.barcode
        id = alt.product_id.id
        if check_i != id or check_b != barcode:
          return False
      return True


    if not item_barcode or not main:
      ## no product has barcode
      return {'item_validity': False, 'alt': None, 'has_main': False, 'product': None}
    
    elif not main.barcode and alts:
      # main product has no barcode, barcode is on alt
      # but multiple alts
      return {'item_validity': check_alt(), 'alt': alts[0], 'has_main': False, 'product': None}

    
    elif main.barcode and alts:
      print('both questionnable')
      return {'item_validity': check_alt(), 'alt': alts[0], 'has_main': True, 'product': main}

    else:
      # only main
      print("only main")
      return {'item_validity': True, 'alt': None, 'has_main': True, 'product': main}

      
      

  def check_item_odoo_existence(self, table: pd.DataFrame) -> dict:
    """CHECKS IF ITEMS TO BE SENT TO ODOO ARE 
      INDEED EXISTING IN ODOO PRODUCT.PRODUCT TABLE
    
    CHECKS CROSS VALIDATION OF PRODUCTS IDs AND BARCODE

    TEST CAN RAISE MANY PROBLEMS DUE TO ODOO DATABASE UNCONSISTENCIES
    @multi_items
    @...
    
    Args:
        table (pd.DataFrame): purchase object Table_done to check

    Returns:
        dict: test valididy
    """
    errors = [] #dict(barode, product, hint placeholder)
    validity = True

    for item in table.values.tolist():
      item_barcode = item[0]
      item_id = item[1] 
      result = self.check_item_alt_integrity(item)
      result['barcode'] = item_barcode
      item_validity = result['item_validity']
      print('__', item_barcode, '-', item_id)
      print('valid__', item_validity)
      
      if item_validity:
        odoo_alt = result['alt']
        if not result['has_main']:
          odoo_barcode = odoo_alt.barcode
          odoo_id = odoo_alt.product_id.id
        else:
          odoo_barcode = self.get('product.product', [('id','=',item_id)]).barcode
          odoo_id = self.get('product.product', [('barcode','=',item_barcode)]).id
          odoo_alts = self.browse('product.multi.barcode', [('product_id','=', item_id)]).barcode
          
        if item_id != odoo_id or (item_barcode != odoo_barcode and item_barcode not in odoo_alts):
          print('_',odoo_barcode, 'has a problem')
          ## ITEM VALIDITY FALSE
          ### CASE BARCODE IS FALSE :: NO BARCODE PRODUCT
          ### CASE ID AND BARCODE DO NOT MATCH
          item_validity = False
          validity = False          
          # test arror handling
          errors.append(format_error_cases("unmatch", result))
          continue
      
      else:
        ## ITEM VALIDITY IS FALSE
        ###CASE ALT == NONE && HAS_MAIN == FALSE: PREDUCT NOT IN ODOO
        ###CASE ALT == NOT NONE && HAS_MAIN == TRUE: PREDUCT HAS DUPLICATES IN MULTI && PROD.PROD
        ###CASE ALT == NOT NONE && HAS_MAIN == FALSE: PREDUCT HAS DUPLICATES INSIDE MULTI BARCODE SUPPOSED NOT HAPPEN HANDLE IT ANYWAY
        # Odoo database problem where a product barcode refer to multiple products...
        print('__', item_barcode, '__')
        item_validity = False
        validity = False        
        #test error handling
        errors.append(format_error_cases("item_validity", result))
        continue
      
    return {'validity': validity, "errors": errors}


  def check_item_purchase_existence(self, purchase, table: pd.DataFrame, create: bool) -> dict:
    """CHECK IF ITEMS ARE INDEED IN ODOO PURCHASE
    
    WHEN product not found and config apply auto item creation, 
    the item will be automatically created,
    otherwise break validation process and request manual item add

    Args:
        purchase (_type_): Purchase object to check
        table (pd.DataFrame): purchase table_done to check
        create (bool): create item or not when unmatched

    Returns:
        dict: test results and valididy
    """
    errors = []
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
          validity = False        
          ## errors handling
          errors.append(format_error_cases("creation_no_exist", 
                                           {
                                            "barcode": item_barcode, 
                                            "product": self.get('product.product', 
                                                                [('id','=',item_id)])
                                            }))
        
      elif item_state == 'none' and create == False:
        validity = False
        ## errors handling
        errors.append(format_error_cases("creation_inactivated", 
                                          {
                                          "barcode": item_barcode, 
                                          "product": self.get('product.product', 
                                                              [('id','=',item_id)])
                                          }))

    return {'validity': validity, "errors": errors}


  def post_products(self, purchase: Purchase):
    """apply received qty in odoo for eachs received items of the purchase"""
    name = purchase.name
    moves = self.browse('stock.move', [('origin', '=', name)])
    for move in moves:
      print('--', move.product_id)
      move_id = move.id
      move_state = move.state
      item_id = move.product_id.id

      if move_state == 'assigned' and purchase.is_received(item_id):
        received_qty = purchase.get_item_received_qty(item_id)
        self.apply_purchase_record_change(move_id, received_qty)


  def post_purchase(self, purchase: Purchase, data: dict, autoval:bool) -> dict:
    """METHOD TO SEND PURCHASE DATA BACK INTO ODOO, APPLYING RECEIVED QTY MODFICATION
      AND AUTO VALIDATION WHEN TRUE
      to avoid any clash, crash and errors back into odoo database, the post processus
      follow restrictive checks that stops the process at any abnormality found.
      
      The post process takes only care about purchase.table_done products,
      table_queue and table_entries are neglected and considered non-relevant.
      
      CHECKS
      @test1: checks if the purchase has not already been manually validated in odoo.
      @test2: checks if all table_done items are existing in odoo product.product table
              in case, where a product do not exist, it is required to manually
              add the product into odoo
      @test3: checks if all items from table_done are existing inside the its original odoo image,
              IF ODOO_CREATE_NEW_PURCHASE_LINE config is True:
                when an unmatched item is found, automatically add it into odoo purchase
              IF ODOO_CREATE_NEW_PURCHASE_LINE config is False:
                when an unmatched item is found, break processus. The item needs 
                to be manually added or removed from the application table
      
      If all test are passed, the data can be safely imported into odoo.
      it take all rpoducts from odoo purchase and apply its new received qty
      
      If autoval is True:
        Propagate the validation event. No manual validation in odoo is recquired.
      If autoval is False:
        Manual validation in odoo is recquired
        
    Args:
        purchase (Purchase): Purchase to be validated
        data (dict): cache data dict
        autoval (bool): wether propagate with an odoo auto validation 
                        or keep manual odoo validation

    Returns:
        dict: validation state dict
    """
    purchase.process_status = 'verified'
    name = purchase.name
    table = purchase.table_done
    
    # ====> verify that the purchase is not already validated
    picking_state = self.get_picking_state(name)
    if picking_state == 'done':
      # already odoo validated, msg this information and block data transfer
      return {'validity': False, 'failed': 'validation_exist', 'errors': ['']} 
    
    # ====> purchase_item exist in ODOO
    odoo_exist = self.check_item_odoo_existence(table)
    if odoo_exist['validity'] == False:
      # DATA VALIDITY IS TO BE PASSED TO ODOO
      return {'validity': False, 'failed': 'odoo_exist', 'errors': odoo_exist['errors']}
    print('test1 passed')

    # <==== room item all in odoo purchase
    purchase_exist = self.check_item_purchase_existence(purchase, table, data['config'].ODOO_CREATE_NEW_PURCHASE_LINE)
    if purchase_exist['validity'] == False:
      # All product from the app are not in the odoo purchase object.
      # purchase items can be create if odoo_create_new_purchase_item == True
      return {'validity': False, 'failed': 'purchase_exist', 'errors': purchase_exist['errors']}
    print('test2 passed')

    # APPLY MODIFICATION TO ODOO ITEMS
    self.post_products(purchase)    
    return {'validity': True, 'failed': 'none', 'errors': []}



  def product_supplier_data(self, purchase, product):
    """retrieve supplier data for requested item
    Price and name
    Informations are nacessary in order to create new item row in odoo purchase
    return product name and price"""
    partner_item = self.get('product.supplierinfo', 
                            [('id','=', purchase.supplier.id), 
                             ('product_tmpl_id.id','=', product.product_tmpl_id.id)
                             ])

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


  def create_purchase_record(self, purchase: Purchase, item_id: int) -> bool:
    """ USED IF ODOO_CREATE_NEW_PURCHASE_LINE=TRUE
    create item row into an odoo purchase.
    
    If the item is not found in product.product, 
    the process fail and break post_purchase test3
    However this case should not happen as test2 has been sucessfull

    Args:
        purchase (Purchase): purchase object
        item_id (int): odoo product.prudct id

    Returns:
        bool: successfully created item
    """
    purchase_id = purchase.id
    product = self.get('product.product', [('id','=',item_id)])
    if not product:
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

    self.create('purchase.order.line', new_item)
    return True


  def recharge_purchase(self, purchase: object, data: dict) -> None:
    """Request to update purchase data from odoo
    keep room table structure untouched
    In use when odoo is modified eg: 
    new product added in odoo, 
    change in quantity, pkg qty, name, barcode
    product supr
    ...
    return purchase object 
    """

    id, name = purchase.id, purchase.name
    purchase_state = self.get('purchase.order', [('id', '=', id)]).state
    picking_state = self.get_picking_state(name) 
    
    if purchase_state == 'purchase' and picking_state == 'assigned':
      ### LOOK FOR UPDATE
      moves = self.browse('stock.move',
                          [('origin', '=', name)])

      for item in moves:
        product = {'id': item.product_id.id,
                  'barcode': self.get_barcode(item),
                  'name': re.sub('\[.*?\]', '', item.name).strip(),
                  'qty': item.product_qty,
                  'qty_packaqe': item.product_qty_package,
                  'qty_received': 0}
        purchase.recharge_item(product, 
                               purchase.process_status, 
                               item.state)
      
    elif purchase_state == 'cancel' or picking_state == 'cancel':
      # CANCELED: REMOVE PURCHASE
      if id in list(data['odoo']['purchases']['incoming'].keys()):
        data['odoo']['purchases']['incoming'].pop(id)

      elif id in list(data['odoo']['purchases']['received'].keys()):
        data['odoo']['purchases']['received'].pop(id)
    

  def delete_purchase(self, id:str, data: dict, object_type: str, state: str):
    """removed purchase from paired list"""
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
  
  



  ########################################### INVENTORY #########################################################
  ###############################################################################################################
  
  def get_product_categories(self, data: dict) -> List[Tuple[str, int]]:
    """Generate list of product categories existing in odoo. sort it by lexicographic order
    
    place the data into the data dict: data['odoo']['inventory']['type']

    Returns:
        List[Tuple[str, int]]: list of tuple name and id of product categories.
    """

    categories = self.browse('product.category', 
                             [(['create_date','>','1900-01-01 01:01:01'])])
    cat = sorted([(c.complete_name, c.id) for c in categories],
                  key=lambda x: x[0],
                  reverse=False)
    
    data['odoo']['inventory']['type'] = cat
    return data   
  
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
    
    columns = ['barcode', 'id', 'name', 'qty', 'virtual_qty', 'qty_received']
    table = pd.DataFrame(product_list, columns= columns)
    table.fillna(0, inplace=True)
    return table



  def create_inventory(self, input:dict, data: dict, table: pd.DataFrame) -> int:
    """ CREATE A PURCHASE OBJECT

    Args:
        input (dict): odoo cat_id 
        data (dict): cache data dict
        table (pd.DataFrame): object origin table 

    Returns:
        int: object_id that reference the object into 
            cache['odoo']['inventory']['ongoing'][object_id]
    """
    def get_id() -> int:
      ongoing = list(data['odoo']['inventory']['ongoing'].keys())
      processed = list(data['odoo']['inventory']['processed'].keys())
      done = list(data['odoo']['inventory']['done'].keys())
      m = max(ongoing + processed + done, default=0)
      return m + 1     
    
    object_id = get_id()
    cat_id = input['object_id']
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inventory = Purchase(object_id,
                         [x[0] for x in data['odoo']['inventory']['type'] if x[1] == cat_id][0], #get name from the categ type list
                         Supplier(None, 'inventaire'),
                         True,
                         'inventory',
                         now,
                         now,
                         'incoming',
                         table)

    data['odoo']['inventory']['ongoing'][object_id] = inventory
    return object_id
 


  def post_inventory(self, inventory:Purchase, data: dict, autoval:bool) -> bool:
    """MAIN AND ONLY INTERACTION PROCESS WITH ODOO FOR INVENTORIES OTHER THAN
      THAN FETCHING TEMPLATE DATA
      INVENTORIES ARE ONLY ADDED INTO ODOO AT VALIDATION PROCESS

    THUS
    !!! PRODUCTS ARE NOT BLOCKED IN ODOO AND CAN BE MANIPULATED, SALED...       !!!
    !!! IT IS STRONGLY RECOMMENDED DURING INVENTORIES TO STOP ANY OTHER PROCESS !!!
    !!! THAT COULD AFFECT INVENTORIED PRODUCTS                                  !!!
    
    STEPS
    @CHECKS if products do exist in odoo product.product table, break the process
            if product is found unmatched. A manual add is recquired to be abble to complete this check
    @CREATE A 'stock.inventory' row that will be used as a container for uour inventoried products
    @CREATE 'stock.inventory/line' for each purchase table_done products
    
    @PROPAGATE START, validate the inventory and its lines.
    @PROPAGATE VALIDATION, optionnal input from user, remove recquired manual validation

    Args:
        inventory (Purchase): purchase object containing related inventory data
        data (Dict): cache data dict

    Returns:
        bool: process state record
    """
    odoo_exist = self.check_item_odoo_existence(inventory.table_done)
    if odoo_exist['validity'] == False:
      # DATA VALIDITY IS TO BE PASSED TO ODOO
      return {'validity': False, 'failed': 'odoo_exist', 'errors': odoo_exist['errors']}
    
    print('test1 passed')
    p1 = self.create_stock_inventory_row(inventory)
    if p1['validity'] == False:
      # fail at creating a stock.inventory row
      return {'validity': False, 'failed': 'inv_row', 'errors': p1['errors']}
    
    p2 = self.create_stock_inventory_line_row(inventory, p1['container'])
    if p2['validity'] == False:
      # fail at creating one or more stock.inventory.line
      return {'validity': False, 'failed': 'inv_line_row', 'errors': p2['errors']}
    
    
    c = self.propagate_start(p2['container'])
    self.propagate_validate(c, autoval)
    return {'validity': True, 'failed': 'none', 'errors': []}



  def create_stock_inventory_row(self, inventory:Purchase):
    """create a 'stock.inventory' container to be filled with inventory lines"""
    date = datetime.now().strftime("%d-%m-%Y")
    name = f'{inventory.name} {date}'
    validity = True
    try:
      container = self.create('stock.inventory', 
                              {'name': name,
                                'filter': 'categories',
                                'location_id': 12
                                })
    except Exception:
      # handle odoo errors on row creation 
      container = None
      validity = False
    
    return {"validity": validity, "container": container, "errors": []}
      
      
  def create_stock_inventory_line_row(self, inventory:Purchase, container: object):
    """Fill the odoo 'stock.inventory' container with 'stock.inventory.line'
    records from purchase.table_done"""
    validity, errors = True, []
    _,_,records = inventory.get_table_records()
    for r in records:
      product = self.get('product.product', [('id', '=', r['id'])])
      uom = product.product_tmpl_id.uom_id.id
      try:
        self.create('stock.inventory.line', 
          {
            'product_qty': r['qty_received'],
            'product_id': r['id'],
            'product_uom_id': uom,
            'location_id': 12,
            'inventory_id': container.id,
          })
        
      except Exception:
        #handle odoo erppeek erros
        validity = False
        errors.append(format_error_cases("inv_block", 
                                         {"barcode": product.barcode, 
                                          "product": product
                                          })
                      )
 
    return {"validity": validity, "container": container, "errors": errors}

  def propagate_start(self, container:object):
    """use odoo action_start method to propagate inventory creation events"""
    container.action_start()
    return container

  def propagate_validate(self, container:object, autoval:bool):
    """use odoo action_validate methdod to automaticaly validate an inventory"""
    if autoval:
      try:
        container.action_validate()
      except Exception:
        # catch marshall error & pass it
        pass





  #################### BUILD ##############################
  def build(self, data: dict, url:str, login:str, password:str, db:str, verbose:bool, timeDelta: list[int]) -> dict:
    """Building base dataset
    activate only on first activation of the server"""
    self.connect(url, login, password, db, verbose)
    data = self.get_purchase(timeDelta, data)
    data = self.get_product_categories(data)
    self.builded = True
    return data
