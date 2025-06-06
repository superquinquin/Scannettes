from __future__ import annotations
from os import environ
from typing import Any, Dict, Optional
import logging
from flask import Flask
from flask_socketio import SocketIO

from scannettes.tools.authenticator import Authenticator
from scannettes.tools.parsers import get_config, parse_client_config
from scannettes.tools.backup import BackUp, Update, Cache
from scannettes.tools.log import Logger, SimpleStreamLogger
from scannettes.tools.utils import pack


Payload = Dict[str,Any]


banner = """\
      ___           ___           ___           ___           ___           ___                                       ___           ___
     /\__\         /\__\         /\  \         /\  \         /\  \         /\__\                                     /\__\         /\__\ 
    /:/ _/_       /:/  /        /::\  \        \:\  \        \:\  \       /:/ _/_         ___           ___         /:/ _/_       /:/ _/_
   /:/ /\  \     /:/  /        /:/\:\  \        \:\  \        \:\  \     /:/ /\__\       /\__\         /\__\       /:/ /\__\     /:/ /\  \ 
  /:/ /::\  \   /:/  /  ___   /:/ /::\  \   _____\:\  \   _____\:\  \   /:/ /:/ _/_     /:/  /        /:/  /      /:/ /:/ _/_   /:/ /::\  \ 
 /:/_/:/\:\__\ /:/__/  /\__\ /:/_/:/\:\__\ /::::::::\__\ /::::::::\__\ /:/_/:/ /\__\   /:/__/        /:/__/      /:/_/:/ /\__\ /:/_/:/\:\__\ 
 \:\/:/ /:/  / \:\  \ /:/  / \:\/:/  \/__/ \:\~~\~~\/__/ \:\~~\~~\/__/ \:\/:/ /:/  /  /::\  \       /::\  \      \:\/:/ /:/  / \:\/:/ /:/  /
  \::/ /:/  /   \:\  /:/  /   \::/__/       \:\  \        \:\  \        \::/_/:/  /  /:/\:\  \     /:/\:\  \      \::/_/:/  /   \::/ /:/  /
   \/_/:/  /     \:\/:/  /     \:\  \        \:\  \        \:\  \        \:\/:/  /   \/__\:\  \    \/__\:\  \      \:\/:/  /     \/_/:/  /
     /:/  /       \::/  /       \:\__\        \:\__\        \:\__\        \::/  /         \:\__\        \:\__\      \::/  /        /:/  /
     \/__/         \/__/         \/__/         \/__/         \/__/         \/__/           \/__/         \/__/       \/__/         \/__/

                                            Flask v2.2.3    Flask-SocketIO v5.3.2
                                uwsgi v2.0.22   gevent-websocket v0.10.1    gevent v23.9.1
                                                    ERPpeek v1.7.1
"""




class Scannettes(object):
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
        app: Payload,
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
        self.print_banner(locals())

        cache = None
        self.env = env

        if socketio.get("app"):
            raise KeyError(
                "cannettes use socketio init_app, please consider removing app from socketio"
            )
        self.socketio = SocketIO(**socketio)

        if logger:
            logging = Logger(**logger)
        else:
            logging = SimpleStreamLogger()

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
        self.app.config.update({k.upper(): v for k, v in {**app, **flask}.items()})

        import scannettes.handlers.routes as routes
        self.app.register_blueprint(routes.scannettes_bp)

        parse_client_config("./scannettes/static/js/common/config.js", app, camera, styles, options)
        self.pack_client()

        self.app.users = users
        self.app.cache = cache
        self.socketio.init_app(self.app)

    def __call__(self, *args: Any, **kwds: Any) -> None:
        self.socketio.run(self.app, port=8000)

    @classmethod
    def create_app(cls) -> Scannettes:
        cfg = get_config(
            environ.get("CONFIG_FILEPATH", "./scannettes_configs/scannettes_config.yaml")
        )
        return cls(**cfg)

    def print_banner(self, configs: Payload):
        print(banner)
        print(f"Booting {configs['env']} ENV")

    def start_backup_cycle(self, backup: Payload, cache: Cache, logging: logging) -> BackUp:
        logging.info("Initializing Backup system...")
        freq = backup.get("frequency", None)
        fname = backup.get("filename", None)

        if fname is None:
            raise KeyError("Configure a backup file name")
        if fname.split('.')[-1] != "pickle":
            raise ValueError("Only pickle files are currently handled.")
        if freq is None:
            raise KeyError("configure backup frequency [days, hours, mins, secs]")

        bckup = BackUp(fname, freq)
        bckup.BACKUP_RUNNER(cache, logging)
        return bckup

    def build_backend(self, building: Optional[Payload], configs: Payload, logger: logging) -> Cache:
        preference, fname = "bare", None
        if building:
            preference = building.get("prefered_method", "bare")
            fname = building.get('filename', None)

        logging.info(f"prefered method: {preference}... Starting building app backend")
        if preference not in ["backup", "bare"]:
            raise ValueError("prefered method must either 'backup' or 'bare'")
        if preference == "backup" and fname is None:
            logger.warning("no backup filename provided... Starting bare initialization")
            preference = "bare"
        if preference == "backup" and Cache.check_backup_file(fname) is False:
            logging.warning("backup file not found... Switching to bare initialization")
            preference = "bare"
        elif preference == "backup" and Cache.check_backup_file(fname):
            logging.info(f"Loading backup...")
        elif preference == "bare":
            logging.info("Starting bare initialization...")
        return Cache.initialize(method=preference, configs=configs, backup_fname=fname, logging=logging)


    def pack_client(self) -> None:
        pack(
            './scannettes/static/css/common',
            './scannettes/static/css/lobby',
            outfile="./scannettes/static/css/pack/lobby.css"
        )
        pack(
            './scannettes/static/css/common',
            './scannettes/static/css/room',
            outfile="./scannettes/static/css/pack/room.css"
        )

        pack(
            './scannettes/static/js/common',
            './scannettes/static/js/room',
            outfile="./scannettes/static/js/pack/room.js",
            priority= ["config.js", "callbacks.js"]
        )

        pack(
            './scannettes/static/js/common',
            './scannettes/static/js/lobby',
            outfile="./scannettes/static/js/pack/lobby.js",
            priority= ["config.js", "callbacks.js"]
        )
