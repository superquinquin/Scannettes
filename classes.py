import os
import sys
import ssl 
import time
import base64
import erppeek
import traceback
import numpy as np
import pandas as pd
from datetime import datetime
from pyzbar.pyzbar import decode
from dateutil.relativedelta import *
from flask_socketio import emit, join_room
ssl._create_default_https_context = ssl._create_unverified_context # Temporary just because i somehow have ssl problem everytime
pd.options.mode.chained_assignment = None

from config import config


data = {}


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


  def search_product_from_ean(self, code_ean):
    return self.client.model(config['table_product']).browse([('barcode', '=', code_ean)])

  def get_purchase(self, timeDelta):
    global data

    incoming = list(data['odoo']['purchases']['incoming'].keys())
    received = list(data['odoo']['purchases']['received'].keys())
    Y, M, W, D = timeDelta[0], timeDelta[1], timeDelta[2], timeDelta[3]


    date_ceiling = (datetime.now().date() + 
                    relativedelta(years=-Y ,months=-M, weeks=-W, days=-D)).strftime("%Y-%m-%d %H:%M:%S")
    
    
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


  def get_inventory(self):
    global data
    pass



  def build(self, url, login, password, db, verbose, timeDelta):
    """Building base dataset
    activate only on first activation of the server"""
    self.connect(url, login, password, db, verbose)
    self.get_purchase(timeDelta)
    self.get_inventory()


    self.builded = True







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
    self.process_status = None              # [None ,started, finished, verified] None > started > finished, 
                                            # when None, processing tables are not builded
                                            # On started processing tables are builded and at least partially filled
                                            # on finished processing tables are frozen into their current state
    self.table_entries = None
    self.table_queue = None
    self.table_done = None




  def build_process_tables(self):
    """build purchase starting position or reset position"""

    self.scanned_barcodes = []
    self.new_items = []
    self.table_entries = self.table
    self.table_queue = pd.DataFrame([], columns= list(self.table.columns))
    self.table_done = pd.DataFrame([], columns= list(self.table.columns))

    self.process_status = 'started'


  def table_position_to_html(self):
    html_entry_table = self.table_entries.to_html(buf=None, header=True, index=False, justify='left', classes='entry_table').replace('class', 'id')
    html_table_queue = self.table_queue.to_html(buf=None, header=True, index=False, justify='left', classes='queue_table').replace('class', 'id')
    html_table_done = self.table_done.to_html(buf=None, header=True, index=False, justify='left', classes='done_table').replace('class', 'id')

    return html_entry_table, html_table_queue, html_table_done









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



  def barcode_decoder(self, imageData, room_id, room, odoo):
    global data, Odoo

    image = self.decoder(imageData)
    image = np.array(image)
    ean = decode(image)
    if ean:
      code_ean = ean[0].data.decode("utf-8")

      if code_ean not in self.purchase.scanned_barcodes:
        self.purchase.scanned_barcodes.append(code_ean)

        context = self.search_scanned_item(code_ean, odoo)
        context['room_id'] = room_id

        join_room(room_id)
        emit('move_product_to_queue', context, broadcast=True, include_self=True, to=room_id)
        emit('change_color', broadcast=False, include_self=True, to=room_id)
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



  def search_scanned_item(self, code_ean, odoo):
    
    product = self.purchase.table_entries[(self.purchase.table_entries['barcode'] == code_ean)]
    if product.empty: 
      # barcode not in purchase
      new_item = True
      product = odoo.search_product_from_ean(code_ean)

      if not product:
        # barcode not in odoo
        product_id, product_name, product_qty, product_pkg_qty, product_received_qty = 0,'', 0, 0, 0
      
      else:
        #barcoed in odoo
        product_id = product.product_tmpl_id.id[0]
        product_name = product.name[0]
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
    context = {'code_ean': code_ean,
               'product_id': product_id,
               'product_name': product_name,
               'product_qty':  product_qty,
               'product_pkg_qty': product_pkg_qty,
               'product_received_qty': product_received_qty,
               'new_item': new_item}

    return context  



  def update_table_on_edit(self, context):
    global data

    product_id = int(context['product_id'])
    product_barcode = context['barcode']
    product_received = context['newqty']
    from_table = context['table']

    if product_barcode not in self.purchase.scanned_barcodes:
      self.purchase.scanned_barcodes.append(product_barcode)

    if from_table != 'dataframe done_table':
      if from_table == 'dataframe entry_table':
        product = self.purchase.table_entries[(self.purchase.table_entries['barcode'] == product_barcode) | (self.purchase.table_entries['id'] == product_id)]
        product.loc[product.index, 'qty_received'] = product_received

        self.purchase.table_done = pd.concat([self.purchase.table_done, product], ignore_index=True)
        self.purchase.table_entries = self.purchase.table_entries.drop(product.index, axis=0)
        self.purchase.table_entries = self.purchase.table_entries.reset_index(drop=True)

      else:
        product = self.purchase.table_queue[(self.purchase.table_queue['barcode'] == product_barcode) | (self.purchase.table_queue['id'] == product_id)]
        product.loc[product.index, 'qty_received'] = product_received

        self.purchase.table_done = pd.concat([self.purchase.table_done, product], ignore_index=True)
        self.purchase.table_queue = self.purchase.table_queue.drop(product.index, axis=0)
        self.purchase.table_queue = self.purchase.table_queue.reset_index(drop=True)
    
    else:
      product = self.purchase.table_done[(self.purchase.table_done['barcode'] == product_barcode) | (self.purchase.table_done['id'] == product_id)]
      self.purchase.table_done.loc[product.index, 'qty_received'] = product_received

    join_room(context['roomID'])
    # broadcasting update
    emit('broadcast_update_table_on_edit', context, broadcast=True, include_self=False, to=context['roomID'])


  def update_table_on_scan(self):
    pass










class User:
  def __init__(self, id, loc, admin):
    self.id = id
    self.location = loc  # [lobby, roomID]
    self.admin = admin
    self.session = 1
    self.is_active = True

  def is_admin(self):
    self.admin = True








class Log:
  def __init__(self):
    folder = os.path.dirname(__file__)
    self.log = open(folder+'/log.log', 'a', encoding='utf-8', errors='ignore')

  def handle_log(self, ip, user, request):
    self.log.write(f'{ip} {user} {datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")} {request}')

  def handle_error_log(self, ip, user, error):
    self.log.write(f'{ip} {user} {datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")} {error}')

