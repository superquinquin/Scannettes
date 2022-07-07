from .odoo import Odoo
from .lobby import Lobby


def init_ext(data):

  config = data['config']
    
  odoo = Odoo()
  lobby = Lobby()
  
  data = odoo.build(data,
                    config.API_URL, 
                    config.SERVICE_ACCOUNT_LOGGIN, 
                    config.SERVICE_ACCOUNT_PASSWORD, 
                    config.API_DB, 
                    config.API_VERBOSE, 
                    config.DELTA_SEARCH_PURCHASE)
  

  return data, odoo, lobby

  
  