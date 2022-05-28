
from .odoo import Odoo
from .lobby import Lobby
from .log import Log
from .backup import BackUp
from .purchase import Purchase
from .room import Room
from .user import User



def init_ext(config):
  global data
  
  odoo = Odoo()
  lobby = Lobby()
  odoo.build(config.API_URL, 
             config.SERVICE_ACCOUNT_LOGGIN, 
             config.SERVICE_ACCOUNT_PASSWORD, 
             config.API_DB, 
             config.API_VERBOSE, 
             config.DELTA_SEARCH_PURCHASE)

  if config.BUILD_ON_BACKUP: 
    config = config
    data = BackUp.load_backup(config.BACKUP_FILENAME)
    config = config
    
  log = Log()
  BackUp().BACKUP_RUNNER()
  odoo.UPDATE_RUNNER()
  
  return odoo, lobby, log

