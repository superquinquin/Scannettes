from gevent import monkey
monkey.patch_all()

import scannettes.handlers.events  # noqa: F401
from scannettes import scannettes

app = scannettes.app
if __name__ == "__main__":
    scannettes()
# http://localhost:5000/lobby
