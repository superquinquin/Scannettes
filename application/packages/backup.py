import time
from threading import Timer
from pickle import dump, load, HIGHEST_PROTOCOL
from xmlrpc.client import ProtocolError

from application.packages.utils import get_delay




class Data(object):

  @classmethod
  def init_data(self, config):
    if config.BUILD_ON_BACKUP == True:
      data = BackUp().load_backup(config)
    
    if config.BUILD_ON_BACKUP == False or data == None:
      data = {'config': config,
              
              'odoo':  {'history':{'update_purchase': [],
                                    'update_inventory': []},

                        'purchases': {'incoming':{},
                                      'received': {},
                                      'done': {},
                                      'draft': {},
                                      'pseudo-purchase': {}},

                          'inventory': {}},
              
              'lobby': {'rooms': {},
                        'users': {'admin': {}}}
              } 
      data['config'] = config

    return data
    






class BackUp:

  def save_backup(self, data, fileName):
    with open(fileName, 'wb') as f:
      dump(data, f, protocol= HIGHEST_PROTOCOL)
      # json.dump(data, fileName)


  def load_backup(self, config):
    # global data
    print('loading backup')
    try:
      with open(config.BACKUP_FILENAME, 'rb') as f:
        data = load(f)
        data['config'] = config
    
    except (FileNotFoundError or EOFError) as e:
      data = None
    
    return data

  def BACKUP_RUNNER(self, config):
    delay = get_delay(delta= config.BACKUP_FREQUENCY)
    print(f'new start in : {delay} seconds')
    timer = Timer(delay, self.BACKUP)
    timer.start()

  def BACKUP(self):
    from application import data
    
    self.save_backup(data, data['config'].BACKUP_FILENAME)
    self.BACKUP_RUNNER(data['config'])






class Update:
  
  def __init__(self, odoo) -> None:
    self.odoo = odoo
  
  def UPDATE_RUNNER(self, config):
    """THREADING and schedulding update every XXXX hours
    possibly placed under build"""
    delay = get_delay(time= config.BUILD_UPDATE_TIME) #time
    print(f'new update in : {delay} seconds')
    timer = Timer(delay, self.update_build)
    timer.start()


  def update_build(self):
    from application import data
    
    while True:
      try:
        data = self.odoo.get_purchase(data['config'].DELTA_SEARCH_PURCHASE, data)
        self.odoo.get_inventory()
        self.UPDATE_RUNNER(data['config'])
        break
      
      except ProtocolError as pe:
        time.sleep(60)

      except KeyError as ke:
        self.UPDATE_RUNNER(data['config'])
        break
        
