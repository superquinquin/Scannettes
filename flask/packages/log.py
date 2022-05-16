from os.path import dirname
from datetime import datetime



class Log:
  def __init__(self):
    folder = dirname(__file__)
    self.log = open(folder+'/log.log', 'a', encoding='utf-8', errors='ignore')

  def handle_log(self, ip, user, request):
    self.log.write(f'{ip} {user} {datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")} {request}')

  def handle_error_log(self, ip, user, error):
    self.log.write(f'{ip} {user} {datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")} {error}')