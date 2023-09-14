

import sys
from flask import Flask
from flask_socketio import SocketIO
from typing import Dict, List, Any, Optional


from cannettes.packages.backup import Caching, BackUp, Update
from cannettes.packages.log import Log

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
    :socketio: configuration for flask-socketio
    :odoo: configuration for connecting to Odoo erp api
    :backup: configuration for handling cache backup
    :logger: configuration for logging system
    :mailling: configuration for automatique mailling
    :options: cannettes systems options for handling diverse setup
    :camera: camera configuration for handling front end and backend camera scanning
    :style: front end design options configurations
    """
    
    
    def __init__(
        self,
        *,
        flask: Dict[str, Any],
        odoo: Dict[str, Any],
        camera: Dict[str, Any],
        socketio: Optional[Dict[str, Any]]= {},
        backup: Optional[Dict[str, Any]]= None,
        logger: Optional[Dict[str,Any]]= None,
        mailling: Optional[Dict[str, Any]]= None,
        options: Optional[Dict[str, Any]]= None,
        style: Optional[Dict[str, Any]]= None
        ) -> None:
        
        cache = Caching()
        cache.init_cache()
        
        if socketio.get("app"):
            raise KeyError("cannettes use socketio init_app, please consider removing app from socketio")
        self.socketio = SocketIO(**socketio)
        
        
        if logger:
            pass    
        
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
        else:
            cache.set_config(locals())
            self.cache = cache()

        # -- fetch Odoo
        

        if not flask.get("static_url"):
            raise KeyError("you must set a static path for Flask")
        self.app = Flask(__name__, static_url_path= flask.get("static_url"))
        self.app.config.update({k.upper():v for k,v in flask})
        self.socketio.init_app(self.app)

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        print(banner)
        self.socketio.run(self.app)
        