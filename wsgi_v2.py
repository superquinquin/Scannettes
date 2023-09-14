import yaml
from yaml import SafeLoader
from gevent import monkey
monkey.patch_all()

from cannettes_v2.main import cannette
# from cannettes_v2.main import Cannettes
# from cannettes_v2.parsers import parse_config

# cfg = parse_config(yaml.load(open("cannettes_configs/cannettes_config.yaml"), SafeLoader))
# cannette = Cannettes(**cfg)

if __name__ == "__main__":
    cannette()
    # http://localhost:5000/lobby
