import os
import sys
import ssl 
import time
import base64
import erppeek
import binascii
import traceback
import numpy as np
import pandas as pd
from warnings import warn
from datetime import datetime
from pyzbar.pyzbar import decode
from dateutil.relativedelta import *
from flask_socketio import emit, join_room
ssl._create_default_https_context = ssl._create_unverified_context
pd.options.mode.chained_assignment = None

from threading import Timer
from pickle import dump, load, HIGHEST_PROTOCOL

from config import config
from utils import get_delay


data = {'cache': {'pos_max_id': None}}

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
    return self.client.model(config['table_product']).get([('id', '=', product_id)])



  def search_product_from_ean(self, code_ean):
    """search for product object in product table."""
    return self.client.model(config['table_product']).get([('barcode', '=', code_ean)])



  def search_alternative_ean(self, code_ean):
    """search in multi_barcode for scanned ean
    return product linked to main ean"""
    alt_product = self.client.model(config['table_alternative_product']).get([('barcode','=',code_ean)])
    if alt_product is not None:
      return self.client.model(config['table_alternative_product']).get([('barcode','=',code_ean)]).product_id

    else:
      return None


  def search_item_tmpl_id_from_product_id(self, product_id):
    return self.client.model(config['table_product']).get([('id','=', product_id)]).product_tmpl.id

  def search_item_UOM(self, product_tmpl_id):
    return self.client.model(config['table_tmpl']).get([('id','=', product_tmpl_id)]).uom_id.id

  def search_item_base_price(self, product_tmpl_id): 
    res_partner_id = self.client.model(config['table_supplier']).get([('product_tmpl_id.id','=', product_tmpl_id)]).name.id
    base_price = self.client.model(config['table_supplier']).get([('name','=',res_partner_id),('product_tmpl_id.id','=', product_tmpl_id)]).base_price
    return base_price

  def generate_purchased_item_name(self, product_tmpl_id):
    product_name = self.client.model(config['tables_product']).get([('id','=',13847)]).name
    res_partner_id = self.client.model(config['table_supplier']).get([('product_tmpl_id.id','=', product_tmpl_id)]).name.id
    product_code = self.client.model(config['table_supplier']).get([('name','=',res_partner_id),('product_tmpl_id.id','=', product_tmpl_id)]).product_code
    
    return f'[{product_code}] {product_name}'


  def apply_purchase_record_change(self, table, order_id, item_id, received_qty, is_recordList):
    if is_recordList == False:
      item = self.client.model(table).get([('order_id', '=', order_id),('product_id.id','=', item_id)])
      item.qty_received = received_qty
    
    else:
      for item in self.client.model(table).browse([('order_id', '=', order_id),('product_id.id','=', item_id)]):
        item.qty_received = received_qty



  def check_input_validity(self, table):
    validity = True

    for item in table.values.tolist():
      item_validity = True
      item_barcode = item[0]
      item_id = item[1]

      from_id = self.search_product_from_id(item_id)
      from_ean = self.search_product_from_ean(item_barcode)
      from_ean_alt = self.search_alternative_ean(item_barcode)


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

    return validity




  def get_purchase(self, timeDelta):
    global data

    incoming = list(data['odoo']['purchases']['incoming'].keys())
    received = list(data['odoo']['purchases']['received'].keys())
    Y, M, W, D = timeDelta[0], timeDelta[1], timeDelta[2], timeDelta[3] # YEAR, MONTH, WEEK, DAY

    if not data['odoo']['history']['update_purchase']:
      date_ceiling = (datetime.now().date() + 
                      relativedelta(years=-Y ,months=-M, weeks=-W, days=-D)).strftime("%Y-%m-%d %H:%M:%S")
    else:
      date_ceiling = data['odoo']['history']['update_purchase'][-1]
    
    
    for pur in self.client.model(config['table_purchase']).browse([('create_date', '>', date_ceiling)]):
      items, is_received = [], False

      id = pur.id
      name = pur.name
      create_date = pur.create_date                                    # date purchase is created in odoo
      added_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # date purchase is added in here
      
      print(name,'-', create_date)
      if id not in incoming + received:
        for item in self.client.model(config['table_purchase_lines']).browse([('order_id', '=', id)]):
          item_id = item.product_id.id
          item_barcode = item.product_id.barcode
          item_name = item.name
          item_qty = item.product_qty
          item_qty_packaqe = item.product_qty_package
          item_qty_received = item.qty_received
          # item_product_template_id = item.product_id.product_tmpl_id.id
          items.append([item_barcode, item_id, item_name, item_qty, item_qty_packaqe, item_qty_received])
          
          if item_qty_received > 0:
            is_received = True

        table = pd.DataFrame(items, columns=['barcode', 'id', 'name', 'qty', 'pckg_qty', 'qty_received'])

        if is_received == False:
          status = 'incoming'
          data['odoo']['purchases']['incoming'][id] = Purchase(id, name, create_date, added_date, status, table)

        else:
          status = 'received'
          data['odoo']['purchases']['received'][id] = Purchase(id, name, create_date, added_date, status, table)
      
    data['odoo']['history']['update_purchase'].append(datetime.now().date().strftime("%Y-%m-%d %H:%M:%S"))
    print(data['odoo'])


  def post_purchase(self, room):
    global data

    room.purchase.process_status = 'verified'
    purchase_id = room.purchase.id
    purchase_new_items = room.purchase.new_items
    table = room.purchase.table_done

    if self.check_input_validity(table) == False:
      # DATA VALIDITY IS TO BE PASSED TO ODOO
      return False

    # adding received values
    for item in table.values.tolist():
      item_barcode = item[0]
      item_id = item[1]
      item_received = item[-1]

      if [item_barcode, item_id] in purchase_new_items:
        self.create_purchase_record(room, item_id)
        
      # UPDATE ODOO RECORD.
      try:
        self.apply_purchase_record_change(config['table_purchase_lines'], purchase_id, item_id, item_received, False)

      except ValueError as e:
        # PASS AFFECT CHANGE ON MULTIPLE IDENTICAL RECORDS: VERIFICATION NEED TO BE DONE ON ODOO POST PROCESS
        warn(f'item id {item_id} : plusieurs occurences trouvée. Veuillez vérifier la commandes odoo (commande id : {purchase_id})')
        self.apply_purchase_record_change(config['table_purchase_lines'], purchase_id, item_id, item_received, True)
    
    return True



  def create_purchase_record(self, room, item_id):
    purchase_id = room.purchase.id
    product = self.search_product_from_id(item_id)
    product_tmpl_id = self.search_item_tmpl_id_from_product_id(item_id)
    name = self.generate_purchased_item_name(product_tmpl_id)
    uom = self.search_item_UOM(product_tmpl_id)
    price = self.search_item_base_price(product_tmpl_id)

    new_item = {'order_id': purchase_id,
                'product_uom': uom,
                'price_unit': price,
                'product_qty': 0, #0
                'name': name,
                'product_id': product,
                'date_planned': datetime.now()}

    self.client.model(config['table_purchase_lines']).create(new_item)



  def recharge_purchase(self, purchase):
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

    for item in self.client.model(config['table_purchase_lines']).browse([('order_id', '=', purchase.id)]):
      passed = False
      productData = {'item_id': item.product_id.id,
                     'item_barcode': item.product_id.barcode,
                     'item_name': item.name,
                     'item_qty': item.product_qty,
                     'item_qty_packaqe': item.product_qty_package,
                     'item_qty_received': item.qty_received}


      
      # product_ID would work 99% of the time unless the product has been added through the APP.
      # It then had been surely added thanks to barcode. We need to proceed to barcode search in this case.
      round = 0
      while passed == False:
        if round == 0 or round == 1:
          tableID = 'purchased'
        elif round == 2 or round == 3:
          tableID = 'queue'
        elif round == 4 or round == 5:
          tableID == 'done'

        if round % 2 == 0:
          key = 'id'
          value = productData['item_id']
        else:
          key = 'barcode'
          value = productData['item_barcode']

        print(round, tableID, key, value, productData)
        passed = purchase.update_item(tableID, key, value, productData)

        if round == 6:
          # newly added item in odoo
          passed = purchase.create_new_item(productData)
        
        round += 1






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
    self.get_purchase(config['timeDelta'])
    self.get_inventory()

    self.UPDATE_RUNNER()


  def UPDATE_RUNNER(self):
    """THREADING and schedulding update every XXXX hours
    possibly placed under build"""
    delay = get_delay(time= config['build_update'])
    print(f'new update in : {delay} seconds')
    timer = Timer(delay, self.update_build)
    timer.start()













class Lobby:
  def __init__(self):
    global data

    data['lobby'] = {'rooms': {},
                     'users': {'admin': {}}}

  # Lobby Rooms
  def create_room(self, input):
    global data

    id = input['id']
    name = input['name']
    password = input['password']
    purchase_id = input['pur']
    rayon_id = input['ray']
    data['lobby']['rooms'][id] = Room(id, name, password, purchase_id, rayon_id)

    return data['lobby']['rooms'][id]
  
  def reset_room(self, id):
    global data

    data['lobby']['rooms'][id].purchase.build_process_tables()

  def delete_room(self, id):
    global data

    data['lobby']['rooms'].pop(id)
  

  # Lobby Users
  def create_user(self, context):
    global data

    ip = context['ip']
    id = context['id']
    loc = context['location']
    admin = context['admin']
    data['lobby']['users'][id] = User(ip, id, loc, admin)


  def move_user(self, id, move):
    global data

    data['lobby']['users'][id].location = move

  def delete_user(self, id):
    global data

    data['lobby']['users'].pop(id)











class Purchase:
  """purchase and aisle (when inventory)"""
  
  def __init__(self, id, name, create_date, added_date, status, table):
    self.id = id
    self.name = name
    self.create_date = create_date
    self.added_date = added_date
    self.status = status                     # [incoming, received]
    self.table = table

    # Checking status
    # is init and updated when a Room is created on this purchase
    self.scanned_barcodes = []
    self.new_items = []
    self.mdofied_items = []
    self.process_status = None              # [None ,started, finished, verified] None > started > finished, 
                                            # when None, processing tables are not builded
                                            # On started processing tables are builded and at least partially filled
                                            # on finished processing tables are frozen into their current state
    self.table_entries = None
    self.table_queue = None
    self.table_done = None


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


  def table_position_to_html(self):
    html_entry_table = self.table_entries.to_html(buf=None, header=True, index=False, classes='entry_table').replace('class', 'id').replace('border="1"','')
    html_table_queue = self.table_queue.to_html(buf=None, header=True, index=False, classes='queue_table').replace('class', 'id').replace('border="1"','')
    html_table_done = self.table_done.to_html(buf=None, header=True, index=False, classes='done_table').replace('class', 'id').replace('border="1"','')

    return html_entry_table, html_table_queue, html_table_done

  def get_table_records(self):
    entry_records = self.table_entries.to_dict('records')
    queue_records = self.table_queue.to_dict('records')
    done_records = self.table_done.to_dict('records')

    return entry_records, queue_records, done_records
  
  def append_new_items(self, barcode):
    if barcode not in self.new_items:
      self.new_items.append(barcode)

  def append_modified_items(self, barcode):
    if barcode not in self.modified_items:
      self.modified_items.append(barcode)

  def append_scanned_items(self, barcode):
    if barcode not in self.scanned_barcodes:
      self.scanned_barcodes.append(barcode) 

  def update_item(self, tableID, key, value, productData):
    """for recharging odoo values into the purchases tables"""
    passed = False
    if tableID == 'purchased':
      table = self.table_entries
    elif tableID == 'queue':
      table = self.table_queue
    elif tableID == 'done':
      table = self.table_done

    if table.where(table[key] == value)[key].values.tolist():
      passed = True
      index = table[table[key] == value].index.tolist()
      table.loc[index, 'barcode'] = productData['item_barcode']
      table.loc[index, 'name'] = productData['item_name']
      table.loc[index, 'qty'] = productData['item_qty']
      table.loc[index, 'pckg_qty'] = productData['item_qty_packaqe']
    
    return passed
  
  def create_new_item(self, productData):
    placeholder = pd.DataFrame([[productData['item_barcode'], 
                                productData['item_id'], 
                                productData['item_name'], 
                                productData['item_qty'], 
                                productData['item_qty_packaqe'], 
                                productData['item_qty_received']]],
       columns= ['barcode', 'id', 'name', 'qty', 'pckg_qty', 'qty_received'])

    self.table_entries = pd.concat([self.table_entries, placeholder], ignore_index=True)

    return True


class Room:
  def __init__(self, id, name, password, purchase_id, rayon_id):
    global data

    # status
    self.id = id
    self.name = name
    self.password = password
    self.status = 'open' # [open, close]
    self.oppening_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    self.closing_date = None
    self.users = 0

    if purchase_id != None:
      self.purchase = data['odoo']['purchases']['incoming'][purchase_id]
    else:
      # create a pseudo-purchase.
      spo_id = 'spo' + str(len(list(data['odoo']['purchases']['pseudo-purchase'].keys())) + 1)
      spo_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      spo_status = 'incoming'
      spo_table = pd.DataFrame([], columns=['barcode', 'id', 'name', 'qty', 'pckg_qty', 'qty_received'])
      data['odoo']['purchases']['pseudo-purchase'][id] = Purchase(spo_id,
                                                                  spo_id,
                                                                  spo_date,
                                                                  spo_date,
                                                                  spo_status,
                                                                  spo_table)
      self.purchase = data['odoo']['purchases']['pseudo-purchase'][id]



  def image_decoder(self, imageData, room_id, room, odoo):
    global data, Odoo

    image = self.decoder(imageData)

    image = np.array(image)
    ean = decode(image)
    if ean:
      code_ean = ean[0].data.decode("utf-8")

      if code_ean not in self.purchase.scanned_barcodes:
        self.purchase.append_scanned_items(code_ean)

        context = self.search_scanned_item(code_ean, odoo)
        context['room_id'] = room_id
        context['scanned'] = self.purchase.scanned_barcodes
        context['new'] = self.purchase.new_items
        context['mod'] = self.purchase.modified_items

        join_room(room_id)
        emit('move_product_to_queue', context, broadcast=True, include_self=True, to=room_id)
        emit('change_color', broadcast=False, include_self=True, to=room_id)
        emit('modify_scanned_item', context, broadcast=False, include_self=True, to=room_id)
        print(code_ean)

      else:
        emit('change_color', broadcast=False, include_self=True, to=room_id)
        print(code_ean, 'is already scanned')



  def decoder(self, data):
    """base64 strings
    decode it into numpy array of shape [n,m,1]"""

    bytes = base64.b64decode(data)
    pixels = np.array([b for b in bytes], dtype='uint8')
    image = np.array(pixels).reshape(config['camera_frame_height'], config['camera_frame_width']).astype('uint8')
    return image


  def laser_decoder(self, laserData, room_id, barcode, room, odoo):
    global data, Odoo

    if barcode not in self.purchase.scanned_barcodes:
      self.purchase.append_scanned_items(barcode)

      context = self.search_scanned_item(barcode, odoo)
      context['room_id'] = room_id
      context['scanned'] = self.purchase.scanned_barcodes
      context['new'] = self.purchase.new_items
      context['mod'] = self.purchase.modified_items

      join_room(room_id)
      emit('move_product_to_queue', context, broadcast=True, include_self=True, to=room_id)
      emit('modify_scanned_laser_item', context, broadcast=False, include_self=True, to=room_id)


    else:
      print(barcode, 'is already scanned')

    


  def search_scanned_item(self, code_ean, odoo):
    """SEARCH the product on odoo table. return Context dictionnary for js formating"""
    
    product = self.purchase.table_entries[(self.purchase.table_entries['barcode'] == code_ean)]
    if product.empty: 
      # barcode not in purchase
      new_item = True
      self.purchase.append_new_items(code_ean)

      alt = odoo.search_alternative_ean(code_ean)

      if alt:
        # alt barcode found, extract product from its product id
        alt_id = alt.id
        product = odoo.search_product_from_id(alt_id)
      else:
        # no alt barcode, search for barcode in odoo
        product = odoo.search_product_from_ean(code_ean)


      if not product:
        # barcode not in odoo
        product_id, product_name, product_qty, product_pkg_qty, product_received_qty = 0,'', 0, 0, 0
      
      else:
        #barcode in odoo
        product_id = product.product_tmpl_id.id
        product_name = product.name
        product_qty, product_pkg_qty, product_received_qty = 0, 0, 0


      placeholder = pd.DataFrame([[code_ean,product_id, product_name, product_qty, product_pkg_qty, product_received_qty]]
                                , columns= ['barcode', 'id', 'name', 'qty', 'pckg_qty', 'qty_received'])
      self.purchase.table_queue = pd.concat([self.purchase.table_queue, placeholder], ignore_index=True)

    else:
      #barcode in purchase
      new_item = False
      self.purchase.table_queue = pd.concat([self.purchase.table_queue, product], ignore_index=True)
      self.purchase.table_entries = self.purchase.table_entries.drop(product.index, axis=0)
      self.purchase.table_entries = self.purchase.table_entries.reset_index(drop=True)
      product_id = product_name = product_qty = product_pkg_qty = product_received_qty = None # only code_ean is useful 

    #broadcasting update
    context = {'barcode': code_ean,
               'id': product_id,
               'name': product_name,
               'qty':  product_qty,
               'pckg_qty': product_pkg_qty,
               'qty_received': product_received_qty,
               'new_item': new_item}

    return context  



  def update_table_on_edit(self, context):
    global data

    product_id = int(context['product_id'])
    product_barcode = context['barcode']
    product_received = context['newqty']
    from_table = context['table']
    atype = context['type']

    self.purchase.append_scanned_items(product_barcode)

    if from_table != 'dataframe done_table':
      if from_table == 'dataframe entry_table':
        product = self.purchase.table_entries[(self.purchase.table_entries['barcode'] == product_barcode) | (self.purchase.table_entries['id'] == product_id)]

        if atype == 'mod': 
          product.loc[product.index, 'qty_received'] = product_received
          self.purchase.append_modified_items(product_barcode)

        self.purchase.table_done = pd.concat([self.purchase.table_done, product], ignore_index=True)
        self.purchase.table_entries = self.purchase.table_entries.drop(product.index, axis=0)
        self.purchase.table_entries = self.purchase.table_entries.reset_index(drop=True)

      else:
        product = self.purchase.table_queue[(self.purchase.table_queue['barcode'] == product_barcode) | (self.purchase.table_queue['id'] == product_id)]
        
        if atype == 'mod': 
          product.loc[product.index, 'qty_received'] = product_received
          self.purchase.append_modified_items(product_barcode)

        self.purchase.table_done = pd.concat([self.purchase.table_done, product], ignore_index=True)
        self.purchase.table_queue = self.purchase.table_queue.drop(product.index, axis=0)
        self.purchase.table_queue = self.purchase.table_queue.reset_index(drop=True)
    
    else:
      product = self.purchase.table_done[(self.purchase.table_done['barcode'] == product_barcode) | (self.purchase.table_done['id'] == product_id)]
      self.purchase.table_done.loc[product.index, 'qty_received'] = product_received

    context['scanned'] = self.purchase.scanned_barcodes
    context['new'] = self.purchase.new_items
    context['mod'] = self.purchase.modified_items

    join_room(context['roomID'])
    # broadcasting update
    emit('broadcast_update_table_on_edit', context, broadcast=True, include_self=True, to=context['roomID'])


  def add_item(self, context):
    global data


    product_id = int(context['product_id'])
    product_name = context['product_name']
    product_barcode = context['code_ean']
    product_received = context['product_received_qty']
    product_qty = context['product_qty']
    product_pkg_qty = context['product_pkg_qty']

    product = pd.DataFrame([[product_barcode, product_id, product_name,
              product_qty, product_pkg_qty, product_received]], 
              columns= self.purchase.table_done.columns)

    self.purchase.append_new_items(product_barcode)
    self.purchase.append_scanned_items(product_barcode)

    self.purchase.table_done = pd.concat([self.purchase.table_done, product], ignore_index=True)

    join_room(context['roomID'])
    # broadcasting update
    emit('broadcasted_added_item', context, broadcast=True, include_self=False, to=context['roomID'])



  def del_item(self, context):
    global data

    from_table = context['fromTable']
    index = context['index']
    

    if from_table == 'scanned-list':
      self.purchase.scanned_barcodes = [x for x in self.purchase.scanned_barcodes 
                                        if x not in self.purchase.table_queue.loc[index, 'barcode'].values.tolist()] # supr barcode from scanned ones

      self.purchase.table_queue = self.purchase.table_queue.drop(index, axis=0)
      self.purchase.table_queue = self.purchase.table_queue.reset_index(drop=True)

    elif from_table == 'purchased-list':
      self.purchase.scanned_barcodes = [x for x in self.purchase.scanned_barcodes 
                                  if x not in self.purchase.table_entries.loc[index, 'barcode'].values.tolist()] # supr barcode from scanned ones

      self.purchase.table_entries = self.purchase.table_entries.drop(index, axis=0)
      self.purchase.table_entries = self.purchase.table_entries.reset_index(drop=True)

    elif from_table == 'verified-list':
      self.purchase.scanned_barcodes = [x for x in self.purchase.scanned_barcodes 
                                        if x not in self.purchase.table_done.loc[index, 'barcode'].values.tolist()] # supr barcode from scanned ones

      self.purchase.table_done = self.purchase.table_done.drop(index, axis=0)
      self.purchase.table_done = self.purchase.table_done.reset_index(drop=True)

    join_room(context['roomID'])
    # broadcasting update
    emit('broadcasted_deleted_item', context, broadcast=True, include_self=True, to=context['roomID'])


  
  def mod_item(self, context):
    global data

    from_table = context['fromTable']
    index = int(context['index']) - 1
    barcode = context['code_ean']
    id = context['product_id']
    name = context['product_name']

    self.purchase.append_modified_items(barcode)

    if from_table == 'dataframe queue_table':
      self.purchase.table_queue.loc[index, 'barcode'] = barcode
      self.purchase.table_queue.loc[index, 'id'] = id
      self.purchase.table_queue.loc[index, 'name'] = name

    else:
      self.purchase.table_done.loc[index, 'barcode'] = barcode
      self.purchase.table_done.loc[index, 'id'] = id
      self.purchase.table_done.loc[index, 'name'] = name


    join_room(context['roomID'])
    # broadcasting update
    emit('broadcasted_mod_item', context, broadcast=True, include_self=True, to=context['roomID'])

  
  def update_status_to_received(self):
    global data

    self.purchase.status = 'received'
    self.purchase.process_status = 'finished'
    self.status = 'close'

    room_id = self.id
    purchase_id = self.purchase.id
    data['odoo']['purchases']['received'][purchase_id] = data['odoo']['purchases']['incoming'][purchase_id]
    data['lobby']['rooms'][room_id].purchase = data['odoo']['purchases']['received'][purchase_id]
    data['odoo']['purchases']['incoming'].pop(purchase_id)


  def update_status_to_verified(self):
    global data, lobby
    
    self.purchase.status = 'received'
    self.purchase.process_status = 'verified'
    self.status = 'close'
    self.closing_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    room_id = self.id
    purchase_id = self.purchase.id
    data['odoo']['purchases']['received'].pop(purchase_id)
    data['lobby']['rooms'].pop(room_id)

    











class User:
  def __init__(self, id, loc, browser_id, admin ):

    self.id = id
    self.token = self.generate_token()
    self.browser_id = browser_id

    self.last_connection = datetime.now()
    self.is_active = True

    self.admin = admin
    self.location = loc  # [lobby, roomID]

    self.session = 1

  def is_admin(self):
    self.admin = True

  def generate_token(self):
    return binascii.hexlify(os.urandom(20)).decode()  






class Log:
  def __init__(self):
    folder = os.path.dirname(__file__)
    self.log = open(folder+'/log.log', 'a', encoding='utf-8', errors='ignore')

  def handle_log(self, ip, user, request):
    self.log.write(f'{ip} {user} {datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")} {request}')

  def handle_error_log(self, ip, user, error):
    self.log.write(f'{ip} {user} {datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")} {error}')




class BackUp:

  def save_backup(self, data, fileName):
    with open(f'./{fileName}.pickle','wb') as f:
      dump(data, f, protocol= HIGHEST_PROTOCOL)

  def load_backup(self, fileName):
    with open(f'./{fileName}.pickle', 'rb') as f:
      data = load(f)
    return data

  def BACKUP_RUNNER(self):
    delay = get_delay(delta= config['backup_frequency'])
    print(f'new start in : {delay} seconds')
    timer = Timer(delay, self.BACKUP)
    timer.start()

  def BACKUP(self):
    global data
    self.save_backup(data, config['backup_fileName'])
    self.BACKUP_RUNNER()