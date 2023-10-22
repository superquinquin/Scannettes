from gevent import monkey

import cannettes_v2.handlers.events  # noqa: F401
from cannettes_v2 import cannette

monkey.patch_all()
cannette()

# if __name__ == "__main__":
#     cannette()
# http://localhost:5000/lobby
