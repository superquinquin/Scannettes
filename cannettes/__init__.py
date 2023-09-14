import sys
from flask import Flask
from flask_socketio import SocketIO
from cannettes.config import define_config, define_client_config, parser
from cannettes.packages import init_ext
from cannettes.packages.log import Log, Hook, ErrLogFlush
from cannettes.packages.backup import Data, BackUp, Update
from cannettes.packages.utils import unify


config = define_config(parser().config)
socketio = SocketIO(async_mode="gevent")  #
data = Data.init_data(config)
data, odoo, lobby = init_ext(data)

# Log(config)
# sys.excepthook = Hook().exception_hook
# sys.stderr = ErrLogFlush(config)

Update(odoo, lobby).UPDATE_RUNNER(config)
BackUp().BACKUP_RUNNER(config)


def create_app(config_name: str = None, main: bool = True) -> Flask:
    global data

    config = define_config(config_name)
    define_client_config(config)
    unify("application/static/js/room", "js", "unified_inventory")
    unify("application/static/js/room", "js", "unified_purchase")
    unify("application/static/js/lobby", "js", "unified")
    unify("application/static/js/login", "js", "unified")

    app = Flask(__name__, static_url_path=config.STATIC_URL)
    app.config.from_object(config)

    import cannettes.packages.routes as routes
    import cannettes.packages.events

    app.add_url_rule("/doc", view_func=routes.doc)
    app.add_url_rule("/lobby", view_func=routes.index)
    app.add_url_rule("/lobby&id=<id>&token=<token>", view_func=routes.index_admin)
    app.add_url_rule("/lobby/login", view_func=routes.login)
    app.add_url_rule(
        "/lobby/<id>&type=purchase&roomtoken=<room_token>",
        view_func=routes.get_purchase_room,
    )
    app.add_url_rule(
        "/lobby/<id>&type=inventory&roomtoken=<room_token>",
        view_func=routes.get_inventory_room,
    )
    app.add_url_rule(
        "/lobby/admin/<id>&type=purchase&roomtoken=<room_token>&id=<user_id>&token=<token>&state=<state>",
        view_func=routes.get_purchase_room_admin,
    )
    app.add_url_rule(
        "/lobby/admin/<id>&type=inventory&roomtoken=<room_token>&id=<user_id>&token=<token>&state=<state>",
        view_func=routes.get_inventory_room_admin,
    )

    socketio.init_app(
        app,
        cors_allowed_origins=config.CORS_ALLOWED_ORIGINS,
        logger=config.LOGGER,
        engineio_logger=config.ENGINEIO_LOGGER,
    )

    return app
