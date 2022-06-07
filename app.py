# import ssl 
# ssl._create_default_https_context = ssl._create_unverified_context
from eventlet import monkey_patch
monkey_patch()

from application import create_app, socketio, data
from application.config import parser, define_config
app = create_app(parser().config)

if __name__ == '__main__':
  socketio.run(app)
  #http://localhost:5000/lobby