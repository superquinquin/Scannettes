from threading import Timer
from pickle import dump, load, HIGHEST_PROTOCOL
import json
from application.packages.utils import get_delay
from application import data

class BackUp:

  def save_backup(self, data, fileName):
    with open(fileName, 'wb') as f:
      dump(data, f, protocol= HIGHEST_PROTOCOL)
      # json.dump(data, fileName)

  def load_backup(self, config):
    global data
    print('loading backup')
    try:
      with open(config.BACKUP_FILENAME, 'rb') as f:
        data = load(f)
        data['config'] = config
    
    except (FileNotFoundError or EOFError) as e:
      # data remain empty
      pass
    
    return data

  def BACKUP_RUNNER(self):
    delay = get_delay(delta= data['config'].BACKUP_FREQUENCY)
    print(f'new start in : {delay} seconds')
    timer = Timer(delay, self.BACKUP)
    timer.start()

  def BACKUP(self):
    global data
    self.save_backup(data, data['config'].BACKUP_FILENAME)
    self.BACKUP_RUNNER()