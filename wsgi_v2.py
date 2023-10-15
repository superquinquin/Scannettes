from gevent import monkey
monkey.patch_all()

from cannettes_v2.main import Cannettes

cannette = Cannettes.create_app()
cannette()

# if __name__ == "__main__":
#     cannette()
    # http://localhost:5000/lobby
