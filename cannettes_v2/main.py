

import sys
import yaml
from yaml import SafeLoader
from flask import Flask, request
from flask_socketio import SocketIO
from typing import Dict, List, Any, Optional

from cannettes_v2.odoo.deliveries import Deliveries
from cannettes_v2.odoo.inventories import Inventories 

from cannettes_v2.odoo.lobby import Lobby
from cannettes_v2.tools.backup import Caching, BackUp, Update
from cannettes_v2.tools.log import Logger
from cannettes_v2.authenticator import Authenticator
from cannettes_v2.utils import unify
from cannettes_v2.parsers import parse_client_config, parse_config

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
        socketio: Dict[str, Any]= {},
        backup: Optional[Dict[str, Any]]= None,
        logger: Optional[Dict[str,Any]]= None,
        authenticator: Optional[Dict[str, Any]]= None,
        mailling: Optional[Dict[str, Any]]= None,
        options: Optional[Dict[str, Any]]= None,
        styles: Optional[Dict[str, Any]]= None
        ) -> None:
        
        self.env = env
        cache = Caching()
        cache.init_cache()
        cache.set_config(locals())
        self.cache = cache()
        
        if socketio.get("app"):
            raise KeyError("cannettes use socketio init_app, please consider removing app from socketio")
        self.socketio = SocketIO(**socketio)
        
        if logger:
            self.logger = Logger(**logger)    
        
        if mailling:
            pass
        

        
        if backup:
            if not backup.get("filename") and not backup.get("frequency"):
                raise KeyError("you must configure a backup filename and backup frequency")
            fname = backup.get("filename")
            freq = backup.get("frequency")
            
            if backup.get("build_on_backup", False):
                cache.load_cache(fname)
                cache.set_config(locals())
                self.cache = cache()
            backup = BackUp(fname, freq)
            backup.BACKUP_RUNNER(self.cache)
            
        if authenticator:
            if not authenticator.get("users_path", None):
                raise FileExistsError("You must configure a user path")
            users = Authenticator().load_users(authenticator["users_path"])

        # -- fetch Odoo
        # self.cache = Deliveries().build(self.cache, **odoo)
        self.cache = Inventories().build(self.cache, **odoo)
        Update(**odoo).UPDATE_RUNNER(self.cache)
        
        if not flask.get("static_url"):
            raise KeyError("you must set a static path for Flask")
        self.app = Flask(__name__, static_url_path= flask.get("static_url"))
        self.app.config.update({k.upper():v for k,v in flask.items()})
        
        import cannettes_v2.handlers.routes as routes
        self.app.register_blueprint(routes.cannettes_bp)
        
        parse_client_config(
            "./cannettes_v2/static/js/config.js",
            flask,
            camera,
            styles
        )
        unify("cannettes_v2/static/js/lobby", "js", "unified")
        unify("cannettes_v2/static/js/login", "js", "unified")
        unify("cannettes_v2/static/js/room", "js", "unified_purchase")
        unify("cannettes_v2/static/js/room", "js", "unified_inventory")     
                
        self.app.users = users
        self.app.cache = self.cache
        self.socketio.init_app(self.app)


    def __call__(self, *args: Any, **kwds: Any) -> Any:
        print(banner)
        self.socketio.run(self.app)




cfg = parse_config(yaml.load(open("cannettes_configs/cannettes_config.yaml"), SafeLoader))
cannette = Cannettes(**cfg)
import cannettes_v2.handlers.events