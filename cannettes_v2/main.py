from os import environ
from typing import Any, Dict, Optional, Union

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
        flask: Dict[str, Any],
        odoo: Dict[str, Any],
        camera: Dict[str, Any],
        socketio: Dict[str, Any] = {},
        backup: Optional[Dict[str, Any]] = None,
        logger: Optional[Dict[str, Any]] = None,
        authenticator: Optional[Dict[str, Any]] = None,
        mailling: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
        styles: Optional[Dict[str, Any]] = None,
    ) -> None:
        cache = None
        self.env = env

        if socketio.get("app"):
            raise KeyError(
                "cannettes use socketio init_app, please consider removing app from socketio"
            )
        self.socketio = SocketIO(**socketio)

        if logger:
            self.logger = Logger(**logger)

        if mailling:
            pass

        if authenticator:
            if not authenticator.get("users_path", None):
                raise FileExistsError("You must configure a user path")
            users = Authenticator().load_users(authenticator["users_path"])

        if backup:
            cache = self.load_cache(backup)
            self.start_backup_cycle(backup, cache)

        if cache is None or cache.check_integrity() is False:
            cache = Cache(config=locals(),lobby=Lobby())
            deliveries = Deliveries.build(cache, odoo)
            inventories = Inventories.build(**odoo)
            cache.update({"deliveries": deliveries, "inventories": inventories})
        Update(**odoo).UPDATE_RUNNER(cache)
        
        if not flask.get("static_url"):
            raise KeyError("you must set a static path for Flask")
        self.app = Flask(__name__, static_url_path=flask.get("static_url"))
        self.app.config.update({k.upper(): v for k, v in flask.items()})


        import cannettes_v2.handlers.routes as routes
        self.app.register_blueprint(routes.cannettes_bp)

        parse_client_config("./cannettes_v2/static/js/config.js", flask, camera, styles)
        unify("cannettes_v2/static/js/lobby", "js", "unified")
        unify("cannettes_v2/static/js/login", "js", "unified")
        unify("cannettes_v2/static/js/room", "js", "unified_purchase")
        unify("cannettes_v2/static/js/room", "js", "unified_inventory")

        self.app.users = users
        self.app.cache = cache
        self.socketio.init_app(self.app)

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        print(banner)
        self.socketio.run(self.app)
        
    @classmethod
    def create_app(cls):
        cfg = get_config(
            environ.get("CONFIG_FILEPATH", "./cannettes_configs/cannettes_config.yaml")
        )
        return cls(**cfg)
    
    def load_cache(self, backup: Dict[str,Any]) -> Union[None, Cache]:
        cache = None
        if not backup.get("filename"):
            raise KeyError("configure filename")
        fname = backup.get("filename")
        
        if backup.get("build_on_backup", False):
            cache = Cache.initialize(fname)
        return cache
    
    def start_backup_cycle(self, backup: Dict[str, Any], cache: Cache) -> BackUp:
        if not backup.get("frequency"):
            raise KeyError("configure backup frequency")
        freq = backup.get("frequency")
        fname = backup.get("filename")
        bckup = BackUp(fname, freq)
        bckup.BACKUP_RUNNER(cache)
        return bckup
        




