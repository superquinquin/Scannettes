import sys
from flask import Flask
from flask_socketio import SocketIO
from application.config import define_config, define_client_config, parser
from application.packages import init_ext
from application.packages.log import Log, Hook, ErrLogFlush
from application.packages.backup import Data, BackUp, Update


config = define_config(parser().config)
socketio = SocketIO(async_mode='gevent') #
data = Data.init_data(config)
data, odoo, lobby = init_ext(data)

# Log(config)
# sys.excepthook = Hook().exception_hook
# sys.stderr = ErrLogFlush(config)

Update(odoo, lobby).UPDATE_RUNNER(config)
BackUp().BACKUP_RUNNER(config)






def create_app(config_name: str = None, main: bool = True) -> Flask :
  global data 
  
  config = define_config(config_name)
  define_client_config(config)  
  
  app = Flask(__name__,
              static_url_path= config.STATIC_URL)
  app.config.from_object(config)
  
  
  import application.packages.routes as routes
  import application.packages.events
  app.add_url_rule('/lobby', view_func= routes.index)
  app.add_url_rule('/lobby&id=<id>&token=<token>', view_func= routes.index_admin)
  app.add_url_rule('/lobby/login', view_func= routes.login)
  app.add_url_rule('/lobby/<id>&roomtoken=<room_token>', view_func= routes.get_room)
  app.add_url_rule('/lobby/admin/<id>&roomtoken=<room_token>&id=<user_id>&token=<token>&state=<state>', view_func= routes.get_room_admin)
  
  socketio.init_app(app, 
                    cors_allowed_origins= config.CORS_ALLOWED_ORIGINS,
                    logger= config.LOGGER,
                    engineio_logger= config.ENGINEIO_LOGGER)
  
  return app
