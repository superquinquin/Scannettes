from flask import Flask
from flask_socketio import SocketIO
from application.config import define_config, define_client_config, parser

socketio = SocketIO()
data = {}


def create_app(config_name: str = None, main: bool = True) -> Flask :
  global data 
  
  config = define_config(config_name)
  define_client_config(config)
    
  app = Flask(__name__,
              static_url_path= config.STATIC_URL)
  app.jinja_env.auto_reload = True
  app.config.from_object(config)
  
  data['config'] = config
  
  import application.packages.routes as routes
  import application.packages.events
  app.add_url_rule('/lobby', view_func= routes.index)
  app.add_url_rule('/lobby&id=<id>&token=<token>', view_func= routes.index_admin)
  app.add_url_rule('/lobby/login', view_func= routes.login)
  app.add_url_rule('/lobby/<id>', view_func= routes.get_room)
  app.add_url_rule('/lobby/admin/<id>&id=<user_id>&token=<token>&state=<state>', view_func= routes.get_room_admin)
  
  socketio.init_app(app, 
                    cors_allowed_origins= config.CORS_ALLOWED_ORIGINS,
                    logger= config.LOGGER,
                    engineio_logger= config.ENGINEIO_LOGGER)
  
  return app
