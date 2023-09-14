from gevent import monkey

monkey.patch_all()

from cannettes import create_app, socketio
from cannettes.config import parser

app = create_app(parser().config)

if __name__ == "__main__":
    socketio.run(app)
    # http://localhost:5000/lobby
