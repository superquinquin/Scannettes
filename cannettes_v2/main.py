from __future__ import annotations
from os import environ
from typing import Any, Dict, Optional, Union

import logging
from flask import Flask
from flask_socketio import SocketIO

from cannettes_v2.authenticator import Authenticator
from cannettes_v2.odoo.deliveries import Deliveries
from cannettes_v2.odoo.inventories import Inventories
from cannettes_v2.odoo.lobby import Lobby
from cannettes_v2.parsers import get_config, parse_client_config
from cannettes_v2.tools.backup import BackUp, Update, Cache
from cannettes_v2.tools.log import Logger
from cannettes_v2.utils import unify

Payload = Dict[str,Any]


banner = """\
      ___           ___           ___           ___           ___                                       ___           ___
     /\__\         /\  \         /\  \         /\  \         /\__\                                     /\__\         /\__\ 
    /:/  /        /::\  \        \:\  \        \:\  \       /:/ _/_         ___           ___         /:/ _/_       /:/ _/_
   /:/  /        /:/\:\  \        \:\  \        \:\  \     /:/ /\__\       /\__\         /\__\       /:/ /\__\     /:/ /\  \ 
  /:/  /  ___   /:/ /::\  \   _____\:\  \   _____\:\  \   /:/ /:/ _/_     /:/  /        /:/  /      /:/ /:/ _/_   /:/ /::\  \ 
 /:/__/  /\__\ /:/_/:/\:\__\ /::::::::\__\ /::::::::\__\ /:/_/:/ /\__\   /:/__/        /:/__/      /:/_/:/ /\__\ /:/_/:/\:\__\ 
 \:\  \ /:/  / \:\/:/  \/__/ \:\~~\~~\/__/ \:\~~\~~\/__/ \:\/:/ /:/  /  /::\  \       /::\  \      \:\/:/ /:/  / \:\/:/ /:/  /
  \:\  /:/  /   \::/__/       \:\  \        \:\  \        \::/_/:/  /  /:/\:\  \     /:/\:\  \      \::/_/:/  /   \::/ /:/  /
   \:\/:/  /     \:\  \        \:\  \        \:\  \        \:\/:/  /   \/__\:\  \    \/__\:\  \      \:\/:/  /     \/_/:/  /
    \::/  /       \:\__\        \:\__\        \:\__\        \::/  /         \:\__\        \:\__\      \::/  /        /:/  /
     \/__/         \/__/         \/__/         \/__/         \/__/           \/__/         \/__/       \/__/         \/__/
"""


class Cannettes(object):
    """
    cannettes wrapper for flask and flask-socketio
    :flask: configurations for flask
    flask configuration: https://flask.palletsprojects.com/en/2.3.x/config/
    :socketio: configuration for flask-socketio
    socketio configuration: https://flask-socketio.readthedocs.io/en/latest/api.html
    :odoo: configuration for connecting to Odoo erp api
    :backup: configuration for handling cache backup
    :logger: configuration for logging system
    :mailling: configuration for automatique mailling
    :options: cannettes systems options for handling diverse setup
    :camera: camera configuration for handling front end and backend camera scanning
    :styles: front end design options configurations
    """

    def __init__(
        self,
        *,
        env: str,
        flask: Payload,
        odoo: Payload,
        camera: Payload,
        socketio: Payload = {},
        building: Optional[Payload] = None,
        backup: Optional[Payload] = None,
        logger: Optional[Payload] = None,
        authenticator: Optional[Payload] = None,
        mailling: Optional[Payload] = None,
        options: Optional[Payload] = None,
        styles: Optional[Payload] = None,
    ) -> None:
        cache = None
        self.env = env

        if socketio.get("app"):
            raise KeyError(
                "cannettes use socketio init_app, please consider removing app from socketio"
            )
        self.socketio = SocketIO(**socketio)

        if logger:
            logging = Logger(**logger)

        if mailling:
            pass

        if authenticator:
            if not authenticator.get("users_path", None):
                raise FileExistsError("You must configure a user path")
            users = Authenticator().load_users(authenticator["users_path"])

        cache = self.build_backend(building, locals(), logging.log)
        cache.set_config(locals())
        
        if backup:
            self.start_backup_cycle(backup, cache, logging.log)
        Update(**odoo).UPDATE_RUNNER(cache, logging.log)
        
        if not flask.get("static_url"):
            raise KeyError("you must set a static path for Flask")
        self.app = Flask(__name__, static_url_path=flask.get("static_url"))
        self.app.config.update({k.upper(): v for k, v in flask.items()})


        import cannettes_v2.handlers.routes as routes
        self.app.register_blueprint(routes.cannettes_bp)

        parse_client_config("./cannettes_v2/static/js/common/config.js", flask, camera, styles)
        # unify("cannettes_v2/static/js/lobby", "js", "unified")
        # unify("cannettes_v2/static/js/login", "js", "unified")
        # unify("cannettes_v2/static/js/room", "js", "unified_purchase")
        # unify("cannettes_v2/static/js/room", "js", "unified_inventory")

        self.app.users = users
        self.app.cache = cache
        self.socketio.init_app(self.app)

    def __call__(self, *args: Any, **kwds: Any) -> None:
        print(banner)
        self.socketio.run(self.app)
        
    @classmethod
    def create_app(cls) -> Cannettes:
        cfg = get_config(
            environ.get("CONFIG_FILEPATH", "./cannettes_configs/cannettes_config.yaml")
        )
        return cls(**cfg)
        
    def start_backup_cycle(self, backup: Payload, cache: Cache, logging: logging) -> BackUp:
        logging.info("Initializing Backup system...")
        freq = backup.get("frequency", None)
        fname = backup.get("filename", None)
        
        if fname is None:
            raise KeyError("Configure a backup file name")
        if fname.split('.')[-1] != "json":
            raise ValueError("Only json files are currently handled.")
        if freq is None:
            raise KeyError("configure backup frequency [days, hours, mins, secs]")
        
        bckup = BackUp(fname, freq)
        bckup.BACKUP_RUNNER(cache, logging)
        return bckup
        
    def build_backend(self, building: Optional[Payload], configs: Payload, logger: logging) -> Cache:
        preference = "bare"
        if building:
            preference = building.get("prefered_method", "bare")
            fname = building.get('filename', None)
        
        logging.info(f"prefered method: {preference}... Starting building app backend")
        if preference not in ["backup", "bare"]:
            raise ValueError("prefered method must either 'backup' or 'bare'")
        if preference == "backup" and fname is None:
            logger.warning("no backup filename provided... Starting bare initialization")
            preference = "bare"
        
        if preference == "backup" and Cache.check_backup_file(fname):
            logging.info(f"Loading backup...")
            cache = Cache.initialize(fname)
            if cache is None:
                logger.warning("Something went wrong when loading the backup... Switching to bare initialization")
                preference = "bare"
        elif preference == "backup" and Cache.check_backup_file(fname) is False:
            logging.warning("backup file not found... Switching to bare initialization")
            preference = "bare"

        if preference == "bare":
            logging.info("Starting bare initialization...")
            cache = Cache(config= configs, lobby=Lobby())
            deliveries = Deliveries.build(cache, configs["odoo"])
            inventories = Inventories.build(**configs["odoo"])
            cache.update({"deliveries": deliveries, "inventories": inventories})
        return cache
        
            
            

