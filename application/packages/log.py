import sys
import traceback
from datetime import datetime
from packages.odoo import data



class Log:
  def __init__(self):
    self.log = open(data['config'].LOG_FILENAME, 'a', encoding='utf-8', errors='ignore')

  def handle_log(self, ip, user, request):
    self.log.write(f'{ip} {user} {datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")} {request}')

  def handle_error_log(self, ip, user, error):
    self.log.write(f'{ip} {user} {datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")} {error}')