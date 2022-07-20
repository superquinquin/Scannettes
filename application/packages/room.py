import base64
import numpy as np
import pandas as pd
from datetime import datetime
from pyzbar.pyzbar import decode

from application.packages.purchase import Purchase




class Room:
  
  def __init__(self, id, name, password, purchase_id, rayon_id, data):
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
      self.purchase = self.generate_pseaudo_purchase(data, id)




  def generate_pseaudo_purchase(self, data, id):
    # create a pseudo-purchase.
    spo_id = 'spo' + str(len(list(data['odoo']['purchases']['pseudo-purchase'].keys())) + 1)
    spo_supplier = None
    spo_realness = False
    spo_ptype = 'purchase'
    spo_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    spo_status = 'incoming'
    spo_table = pd.DataFrame([], columns=['barcode', 'id', 'name', 'qty', 'pckg_qty', 'qty_received'])
    
    data['odoo']['purchases']['pseudo-purchase'][id] = Purchase(spo_id,
                                                                spo_id,
                                                                spo_supplier,
                                                                spo_realness,
                                                                spo_ptype,
                                                                spo_date,
                                                                spo_date,
                                                                spo_status,
                                                                spo_table)
    
    return data['odoo']['purchases']['pseudo-purchase'][id]    
    
    
    
  def image_decoder(self, imageData, room_id, room, odoo, data):
    """ 
    state: 0 for no ean found; 1 for new ean ; 2 for ean already scanned
    """
    image = self.decoder(imageData, data)

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
        context['state'] = 1
        print(code_ean)

      else:
        context = {'state': 2}
        print(code_ean, 'is already scanned')
    
    else:
      context = {'state': 0}
    
    return context




  def decoder(self, image_data, data):
    """base64 strings
    decode it into numpy array of shape [n,m,1]"""

    bytes = base64.b64decode(image_data)
    pixels = np.array([b for b in bytes], dtype='uint8')

    image = np.array(pixels).reshape(data['config'].CAMERA_FRAME_HEIGHT, 
                                     data['config'].CAMERA_FRAME_WIDTH).astype('uint8')
    
    return image


  def laser_decoder(self, laserData, room_id, barcode, room, odoo, data):
    """
      state: 1 ok; state 2: already scanned
    """

    if barcode not in self.purchase.scanned_barcodes:
      self.purchase.append_scanned_items(barcode)

      context = self.search_scanned_item(barcode, odoo)
      context['room_id'] = room_id
      context['scanned'] = self.purchase.scanned_barcodes
      context['new'] = self.purchase.new_items
      context['mod'] = self.purchase.modified_items
      context['state'] = 1

    else:
      context = {'state': 2}
      print(barcode, 'is already scanned')
    
    return context




  def search_scanned_item(self, code_ean, odoo):
    """SEARCH the product on odoo table. return Context dictionnary for js formating"""
    
    product = self.purchase.table_entries[(self.purchase.table_entries['barcode'] == code_ean)]
    alt = odoo.search_alternative_ean(code_ean)
    
    if ((product.empty and not alt) or 
        (product.empty and alt and 
         self.purchase.table_entries[(self.purchase.table_entries['barcode'] == alt.barcode)].empty)):
      
      new_item = True
      self.purchase.append_new_items(code_ean)
      product = odoo.search_product_from_ean(code_ean)
      
      if alt:
        # if product has alt, but alt nor main barcode are in purchase 
        # (could happen if scan by mistake the wrong purchase)
        # then use main barcode and enter it inside the purchase a new product
        # next is to the user appreciation.
        product_name = alt.name
        product_id = alt.id
        
      elif product:
        # product in odoo but not in the purchase
        product = odoo.search_product_from_ean(code_ean)
        product_name = product.name
        product_id = product.id
      
      else:
        # barcode never recognized
        product_id, product_name = 0, ''
      
      
      product_qty, product_pkg_qty, product_received_qty = 0, 0, 0
      placeholder = pd.DataFrame([[code_ean,product_id, product_name, product_qty, product_pkg_qty, product_received_qty]]
                          , columns= ['barcode', 'id', 'name', 'qty', 'pckg_qty', 'qty_received'])
      self.purchase.table_queue = pd.concat([self.purchase.table_queue, placeholder], ignore_index=True)
          
    else:  
      if product.empty and alt:
        product = self.purchase.table_entries[(self.purchase.table_entries['barcode'] == alt.barcode)]
        
      #barcode in purchase
      new_item = False
      self.purchase.table_queue = pd.concat([self.purchase.table_queue, product], ignore_index=True)
      self.purchase.table_entries = self.purchase.table_entries.drop(product.index, axis=0)
      self.purchase.table_entries = self.purchase.table_entries.reset_index(drop=True)
      product_id = product.values.tolist()[0][1]
      product_name = product.values.tolist()[0][2]
      product_qty =  product.values.tolist()[0][3]
      product_pkg_qty = product.values.tolist()[0][4]
      product_received_qty =  product.values.tolist()[0][5]
     
     
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
      self.purchase.append_modified_items(product_barcode)

    context['scanned'] = self.purchase.scanned_barcodes
    context['new'] = self.purchase.new_items
    context['mod'] = self.purchase.modified_items

    return context


  def add_item(self, context):
    
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

    return context



  def del_item(self, context):

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

    return context


  
  def mod_item(self, context):

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
      
    return context



  def update_status_to_received(self, data):

    self.purchase.status = 'received'
    self.purchase.process_status = 'finished'
    self.status = 'close'

    room_id = self.id
    purchase_id = self.purchase.id
    data['odoo']['purchases']['received'][purchase_id] = data['odoo']['purchases']['incoming'][purchase_id]
    data['lobby']['rooms'][room_id].purchase = data['odoo']['purchases']['received'][purchase_id]
    data['odoo']['purchases']['incoming'].pop(purchase_id)



  def update_status_to_verified(self, data):
    
    status = self.purchase.status
    self.purchase.status = 'received'
    self.purchase.process_status = 'verified'
    self.status = 'close'
    self.closing_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    room_id = self.id
    purchase_id = self.purchase.id

    data['odoo']['purchases']['done'][purchase_id] = self.purchase
    if status == 'received':
      data['odoo']['purchases']['received'].pop(purchase_id)
    elif status == 'incoming':
      data['odoo']['purchases']['incoming'].pop(purchase_id)
    data['lobby']['rooms'].pop(room_id)
