import pandas as pd
from typing import Union

class Supplier:
  def __init__(self, partner_id, partner_name):
    self.id = partner_id
    self.name = partner_name
    

class Purchase:
  """purchase or inventory"""
  
  def __init__(self, id, name, supplier, realness, ptype, create_date, added_date, status, table):
    self.id = id
    self.name = name
    
    if supplier is None:
      self.supplier = Supplier(None, 
                               None)
    else:
      self.supplier = Supplier(supplier.id, 
                               supplier.name) # partner_id

    self.supplier_name = self.get_supplier_name()
    self.real = realness # bool == > True= based on real purchase or inventory table 
    self.pType = ptype                       # ['purchase', 'inventory']
    self.create_date = create_date
    self.added_date = added_date
    self.status = status                     # [incoming, received]
    self.table = table

    # Checking status
    # is init and updated when a Room is created on this purchase
    self.wrong_items = []                   # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! to be used for wrong name and add color
    self.scanned_barcodes = []
    self.new_items = []
    self.modified_items = []
    self.process_status = None              # [None ,started, finished, verified] None > started > finished, 
                                            # when None, processing tables are not builded
                                            # On started processing tables are builded and at least partially filled
                                            # on finished processing tables are frozen into their current state
    self.table_entries = None
    self.table_queue = None
    self.table_done = None


  def get_supplier_name(self):
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


  def update_item(self, tableID, key, value, productData, passed):
    """for recharging odoo values into the purchases tables"""

    if tableID == 'purchased':
      table = self.table_entries
    elif tableID == 'queue':
      table = self.table_queue
    elif tableID == 'done':
      table = self.table_done
    elif tableID == 'table':
      table = self.table

    if passed == False and table.where(table[key] == value)[key].values.tolist():
      passed = True
      index = table[table[key] == value].index.tolist()
      table.loc[index, 'barcode'] = productData['item_barcode']
      table.loc[index, 'name'] = productData['item_name']
      table.loc[index, 'qty'] = productData['item_qty']
      table.loc[index, 'pckg_qty'] = productData['item_qty_packaqe']
    
    return passed
  

  def create_item(self, table: pd.DataFrame, productData: dict) -> bool:
    """Create product into selected table"""

    placeholder = pd.DataFrame([[productData['item_barcode'], 
                                productData['item_id'], 
                                productData['item_name'], 
                                productData['item_qty'], 
                                productData['item_qty_packaqe'], 
                                productData['item_qty_received']]],
       columns= ['barcode', 'id', 'name', 'qty', 'pckg_qty', 'qty_received'])

    table = pd.concat([table, placeholder], ignore_index=True)

    return True
  

  def delete_item(self, tableID: str, key: str, value: Union[int, str], passed: bool) -> bool:

    if tableID == 'purchased':
      table = self.table_entries
    elif tableID == 'queue':
      table = self.table_queue
    elif tableID == 'done':
      table = self.table_done
    elif tableID == 'table':
      table = self.table

    if passed == False and table.where(table[key] == value)[key].values.tolist():
      passed = True
      index = table[table[key] == value].index.tolist()
      table.drop(index, axis=0)
      table.reset_index(drop=True)

    return passed

  def change_status(self, status:str, process_status:str):
    self.status = status
    self.process_status = process_status
    
    
  def assembler(self, other):
    oth_tb_done = other.table_done.to_dict('records')

    for record in oth_tb_done:
      self.table_done.loc[self.table_done['id'] == record['id'], 'qty_received'] += record['qty_received']
