from gevent import monkey
monkey.patch_all()

import cannettes_v2.handlers.events  # noqa: F401
from cannettes_v2 import cannette


cannette()

# if __name__ == "__main__":
#     cannette()
# http://localhost:5000/lobby
