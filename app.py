from application import create_app, socketio, data
from application.config import parser, define_config

data['config'] = define_config(parser().config)
import application.packages 

app = create_app(parser().config)

if __name__ == '__main__':
  socketio.run(app)
  #http://localhost:5000/lobby