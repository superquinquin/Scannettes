import re
import time
import erppeek
import pandas as pd
from datetime import datetime
from threading import Timer

from application import data
from application.packages.purchase import Purchase
from application.packages.utils import get_ceiling_date, update_item_auto_table_selector, get_delay

pd.options.mode.chained_assignment = None



class Odoo:
  def __init__(self):
    global data
    #STATUS
    self.builded = False
    self.connected = False

    #CONN
    self.client = None
    self.log = None
    self.tz = None
    self.user = None

    # DATA
    data['odoo'] = {'history':{'update_purchase': [],
                       'update_inventory': []},

            'purchases': {'incoming':{},
                          'received': {},
                          'done': {},
                          'draft': {},
                          'pseudo-purchase': {}},

            'inventory': {}}


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




  def search_product_from_id(self, product_id):
    return self.client.model(data['config'].TABLE_PRODUCT).get([('id', '=', product_id)])



  def search_product_from_ean(self, code_ean):
    """search for product object in product table."""
    return self.client.model(data['config'].TABLE_PRODUCT).get([('barcode', '=', code_ean)])



  def search_alternative_ean(self, code_ean):
    """search in multi_barcode for scanned ean
    return product linked to main ean"""
    alt_product = self.client.model(data['config'].TABLE_ALTERNATIVE_PRODUCT).get([('barcode','=',code_ean)])
    if alt_product is not None:
      return self.client.model(data['config'].TABLE_ALTERNATIVE_PRODUCT).get([('barcode','=',code_ean)]).product_id

    else:
      return None


  def search_item_tmpl_id_from_product_id(self, product_id):
    return self.client.model(data['config'].TABLE_PRODUCT).get([('id','=', product_id)]).product_tmpl_id.id





  def apply_purchase_record_change(self, move_id, received_qty):
      move = self.client.model(data['config'].TABLE_MOVE_LINE).get([('move_id.id','=', move_id)])
      move.qty_done = received_qty
    


  def get_picking_state(self, name):

    try:
      picking = self.client.model(data['config'].TABLE_PICKING).get([('origin','=', name)])
      if picking:
        picking_state = picking.state

      else:
        picking_state = 'draft'

    except ValueError as e:
      # multiple picking ID heading towards a purchase.
      # most likely 1st is canceled and next one correct it.
      # state priority : None < Cancel < assigned < done
      picking = self.client.model(data['config'].TABLE_PICKING).browse([('origin','=', name)])
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
      item = self.client.model(data['config'].TABLE_MOVE).get([('origin','=', name), ('product_id.id','=', id)])
      if item:
        item_state = item.state

      else:
        item_state = 'none'

    except ValueError as e:
      # multiple picking ID heading towards a purchase.
      # most likely 1st is canceled and next one correct it.
      # state priority : None < Cancel < assigned < done
      items = self.client.model(data['config'].TABLE_MOVE).browse([('origin','=', name), ('product_id.id','=', id)])
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


  def get_purchase(self, timeDelta: list) -> None:
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
    global data

    draft = list(data['odoo']['purchases']['draft'].keys())
    incoming = list(data['odoo']['purchases']['incoming'].keys())
    received = list(data['odoo']['purchases']['received'].keys())
    done = list(data['odoo']['purchases']['done'].keys())

    date_ceiling = get_ceiling_date(timeDelta, data, 'update_purchase')
    
    purhasesList = (self.client.model(data['config'].TABLE_PURCHASE).browse([('create_date', '>', date_ceiling)]) +
                   self.client.model(data['config'].TABLE_PURCHASE).browse([('id', 'in', draft)]) + 
                   self.client.model(data['config'].TABLE_PURCHASE).browse([('id', 'in', incoming)]) +
                   self.client.model(data['config'].TABLE_PURCHASE).browse([('id', 'in', received)]))
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
          if id in incoming:
            data['odoo']['purchases']['incoming'].pop(id)
          
          elif id in received:
            data['odoo']['purchases']['received'].pop(id)

          elif id in done:
            data['odoo']['purchases']['done'].pop(id)
            

        elif picking_state == 'done':
          # then pass it to done dict adn remove it from previous dict
          if id in incoming:
            data['odoo']['purchases']['done'][id] = data['odoo']['purchases']['incoming'][id]
            data['odoo']['purchases']['incoming'].pop(id)
          
          elif id in received:
            data['odoo']['purchases']['done'][id] = data['odoo']['purchases']['received'][id]
            data['odoo']['purchases']['received'].pop(id)              

        elif picking_state == 'assigned':
          if id not in incoming + received:
            # add purchase to dict
            moves = self.client.model(data['config'].TABLE_MOVE).browse([('origin', '=', name)])
            for item in moves:

              if item.state == 'assigned':   
                item_name = re.sub('\[.*?\]', '', item.name).strip()
                item_id = item.product_id.id
                item_barcode = item.product_id.barcode
                item_qty = item.product_qty
                item_qty_packaqe = item.product_qty_package
                item_qty_received = 0  

                items.append([item_barcode, item_id, item_name, item_qty, item_qty_packaqe, item_qty_received])

            table = pd.DataFrame(items, columns=['barcode', 'id', 'name', 'qty', 'pckg_qty', 'qty_received'])
            data['odoo']['purchases']['incoming'][id] = Purchase(id, name, supplier, True, 'purchase', create_date, added_date, 'incoming', table)
          
          else:
            # in case modification has been made
            if id in incoming:
              purchase = data['odoo']['purchases']['incoming'][id]
              data['odoo']['purchases']['incoming'][id] = self.recharge_purchase(purchase)

            elif id in received:
              purchase = data['odoo']['purchases']['received'][id]
              data['odoo']['purchases']['received'][id] = self.recharge_purchase(purchase)

      elif purchase_state == 'draft':
        data['odoo']['purchases']['draft'][id] = None # Placeholder to keep tracking drafts

      
    data['odoo']['history']['update_purchase'].append(datetime.now().date().strftime("%Y-%m-%d %H:%M:%S"))
    print(data['odoo'])



  def check_item_odoo_existence(self, table: pd.DataFrame) -> dict:
    item_list = []
    validity = True

    for item in table.values.tolist():
      item_validity = True
      item_barcode = item[0]
      item_id = item[1]
      item_name = item[2]

      from_id = self.search_product_from_id(item_id)
      from_ean = self.search_product_from_ean(item_barcode)
      from_ean_alt = self.search_alternative_ean(item_barcode)

      print('____')
      if from_id:
        print('id_',from_id.id, from_id.barcode)
      if from_ean:
        print('ean_',from_ean.id, from_ean.barcode)
      if from_ean_alt:
        print('alt_',from_ean_alt.id, from_ean_alt.barcode)
      print('____')

      if from_id is None:
        print('from_id is none')
        item_validity = False
        validity = False
      
      if (item_barcode and 
          (from_ean is None and from_ean_alt is None)):
        print('from ean is none')
        item_validity = False
        validity = False

      if item_barcode:
        # Cross validation
        if (from_id and 
            from_id.barcode != item_barcode):
          print('wrong barcode from id')
          item_validity = False
          validity = False
        
        if (from_ean and
            from_ean.id != item_id):
          print('wrong id')
          item_validity = False
          validity = False     

        if (from_ean_alt and 
            from_ean_alt.id != item_id):
          print('wrong alt id')
          item_validity = False
          validity = False 
        
        if item_validity == False:
          item_list.append(item_barcode)

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




  def post_purchase(self, purchase) -> dict:
    global data

    purchase.process_status = 'verified'
    id = purchase.id
    name = purchase.name
    new_items = purchase.new_items
    table = purchase.table_done
    
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
    moves = self.client.model(data['config'].TABLE_MOVE).browse([('origin', '=', name)])
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
    partner_item = self.client.model(data['config'].TABLE_SUPPLIER).get([('id','=', purchase.supplier.id),
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
    name, price = self.product_supplier_data(self, purchase, product)

    new_item = {'order_id': purchase_id,
                'product_uom': uom,
                'price_unit': price,
                'product_qty': 1, #0
                'name': name,
                'product_id': product,
                'date_planned': datetime.now()}

    self.client.model(data['config'].TABLE_PURCHASE_LINE).create(new_item)

    return True


  def recharge_purchase(self, purchase) -> None:
    """Request to update purchase data from odoo
    keep room table structure untouched
    In use when odoo is modified eg: 
    new product added in odoo, 
    change in quantity, pkg qty, name, barcode
    product supr
    ...
    return purchase object 
    """
    global data
    id = purchase.id
    name = purchase.name
    purchase_state = self.client.model(data['config'].TABLE_PURCHASE).browse([('id', '=', id)]).state
    picking_state = self.get_picking_state(name) 

    if purchase_state == 'purchase' and picking_state == 'assigned':
      moves = self.client.model(data['config'].TABLE_MOVE).browse([('origin', '=', name)])
      passed = False

      for item in moves:
        if item.state == 'assigned':   
          productData = {'item_id': item.product_id.id,
                        'item_barcode': item.product_id.barcode,
                        'item_name': re.sub('\[.*?\]', '', item.name).strip(),
                        'item_qty': item.product_qty,
                        'item_qty_packaqe': item.product_qty_package,
                        'item_qty_received': 0}
          update_item_auto_table_selector(purchase, productData, purchase.process_status, item.state)
      
    elif purchase_state == 'cancel' or picking_state == 'cancel':
      # remove from data dict
      if id in list(data['odoo']['purchases']['incoming'].keys()):
        data['odoo']['purchases']['incoming'].pip(id)

      elif id in list(data['odoo']['purchases']['received'].keys()):
        data['odoo']['purchases']['received'].pip(id)



  def get_inventory(self):
    global data
    pass
  

  def post_inventory(self):
    global data
    pass


  def build(self, url, login, password, db, verbose, timeDelta):
    """Building base dataset
    activate only on first activation of the server"""
    self.connect(url, login, password, db, verbose)
    self.get_purchase(timeDelta)
    self.get_inventory()

    self.builded = True


  def update_build(self):
    self.get_purchase(data['config'].DELTA_SEARCH_PURCHASE)
    self.get_inventory()

    self.UPDATE_RUNNER()


  def UPDATE_RUNNER(self):
    """THREADING and schedulding update every XXXX hours
    possibly placed under build"""
    delay = get_delay(time= data['config'].BUILD_UPDATE_TIME)
    print(f'new update in : {delay} seconds')
    timer = Timer(delay, self.update_build)
    timer.start()