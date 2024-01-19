from gevent import monkey
monkey.patch_all()

import scannettes.handlers.events  # noqa: F401
from scannettes import scannettes


scannettes()

# if __name__ == "__main__":
#     cannette()
# http://localhost:5000/lobby
