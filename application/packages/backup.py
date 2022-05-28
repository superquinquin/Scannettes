from threading import Timer
from pickle import dump, load, HIGHEST_PROTOCOL

from application import data
from application.packages.utils import get_delay


class BackUp:

  def save_backup(self, data, fileName):
    with open(fileName, 'wb') as f:
      dump(data, f, protocol= HIGHEST_PROTOCOL)

  def load_backup(self, fileName):
    with open(fileName, 'rb') as f:
      data = load(f)
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