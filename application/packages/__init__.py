from .odoo import Odoo
from .lobby import Lobby
from .log import Log
from .backup import BackUp
from .purchase import Purchase
from .room import Room
from .user import User
from application import data


def init_ext():
  global data
  config = data['config']
  
  # if config.BUILD_ON_BACKUP:
  #   BackUp().load_backup(config)
  
  odoo = Odoo()
  lobby = Lobby()
  log = Log()
  
  data = odoo.build( config.API_URL, 
                    config.SERVICE_ACCOUNT_LOGGIN, 
                    config.SERVICE_ACCOUNT_PASSWORD, 
                    config.API_DB, 
                    config.API_VERBOSE, 
                    config.DELTA_SEARCH_PURCHASE)
  
  odoo.UPDATE_RUNNER()
  BackUp().BACKUP_RUNNER() # can't read the backup anyway...

  return odoo, lobby, log

  
  