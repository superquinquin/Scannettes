import sys
from datetime import datetime


class Log(object):
  def __init__(self, config):
    self.terminal = sys.stderr
    self.log = open(config.LOG_FILENAME, 'a', encoding='utf-8')

  def handle_error_log(self, e):
    self.terminal.write(e)
    self.log.write('----------------------------------------------------------\n')
    self.log.write(f'{datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")}\n')
    self.log.write(e)
    self.log.write('----------------------------------------------------------\n')