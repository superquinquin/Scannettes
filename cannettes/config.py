import json
from os import environ
from typing import List, Dict, Union
import argparse


class Config(object):
    # FLASK
    SECRET_KEY: str = (
        environ.get("SECRET_KEY")
        or "f04be23e93490e284f2e5493da95f62f9255867fa744f6710a04fb1f0acbade760dbf32c1436bc0f"
    )
    STATIC_URL: str = "/static"
    APPLICATION_ROOT: str = "/"

    # FLASK-SOCKETIO
    CORS_ALLOWED_ORIGINS: Union[
        str, List[str]
    ] = "*"  # SOCKETIO :: WILDCARD *; IDEAL LIST(URL)

    ADDRESS: str = environ.get("ERPPEEK_ADDRESS", "00.000.000.000")  # SERVER IP ADDRESS

    # ERPPEEK API
    API_URL: str = environ.get("ERPPEEK_API_URL", "https://production.com")
    API_DB: str = environ.get("ERPPEEK_API_DB", "production")

    ## SERVICE ACCOUNT
    SERVICE_ACCOUNT_LOGGIN: str = environ.get(
        "ERPPEEK_SERVICE_ACCOUNT_LOGGIN", "rom88.viry@gmail.com"
    )
    SERVICE_ACCOUNT_PASSWORD: str = environ.get(
        "ERPPEEK_SERVICE_ACCOUNT_PASSWORD", "@Lvsliftdv88)"
    )

    ## ERPPEEK DB TABLES NAMES
    TABLE_PRODUCT: str = "product.product"
    TABLE_TMPL: str = "product.template"
    TABLE_ALTERNATIVE_PRODUCT: str = "product.multi.barcode"
    TABLE_PURCHASE: str = "purchase.order"
    TABLE_PURCHASE_LINE: str = "purchase.order.line"
    TABLE_SUPPLIER: str = "product.supplierinfo"
    TABLE_PICKING: str = "stock.picking"
    TABLE_MOVE: str = "stock.move"
    TABLE_MOVE_LINE: str = "stock.move.line"

    # FILE PATH
    BACKUP_FILENAME: str = "./application/backup.pickle"
    WHITELIST_FILENAME: str = "./application/whitelist.txt"
    LOG_FILENAME: str = "./log/log.log"
    JSON_CONFIG_FILENAME: str = "./application/static/js/config.js"

    # mail
    SMTP_PORT: int = 587
    SMTP_SERVER: str = "smtp-relay.sendinblue.com"
    EMAIL_LOGIN: str = "gestion@superquinquin.net"
    EMAIL_PASSWORD = "4RD6dA7XUqrZ09Gf"
    RECEIVERS: List[str] = ["rom88.viry@gmail.com"]

    # -- ROOM PASSWORD
    ACTIVATE_ROOM_PASSWORD: bool = False

    # COLORS
    COLOR_PRIMARY: str = "#fefa85"
    COLOR_SECONDARY: str = "#3C312E"
    COLOR_TERNARY: str = "#FAEFEF"
    COLOR_NEW_ITEMS: str = "#FD8789"
    COLOR_NEW_ITEMS_IF_EXIST: str = "#B5B3D0"
    COLOR_MOD_ITEMS: str = "#FDC087"
    COLOR_NORMAL_ITEMS: str = "#CFF2E8"

    # CAMERA
    CAMERA_ENABLE_VIDEO: bool = True
    CAMERA_ENABLE_AUDIO: bool = False
    CAMERA_IDEAL_WIDTH: int = 1920
    CAMERA_IDEAL_HEIGHT: int = 1080
    CAMERA_IDEAL_MODE: str = "environment"

    @classmethod
    def define_as_config(self):
        """Standart config object pointing towards selected config references"""

        return self


class ProductionConfig(Config):
    # FLASK
    ENV: str = "production"
    DEBUG: bool = False
    TESTING: bool = False
    TEMPLATES_AUTO_RELOAD: bool = False

    # FLASK-SOCKETIO
    ENGINEIO_LOGGER: bool = True
    LOGGER: bool = True

    # ERPPEEK API
    # ADDRESS: str = '00.000.000.000'                 # SERVER IP ADDRESS
    # API_URL: str = 'https://gestion.superquinquin.fr'
    # API_DB: str = 'superquinquin_production'
    API_VERBOSE: bool = False

    ## POST OPTIONS
    ODOO_CREATE_NEW_PURCHASE_LINE: bool = True
    ODOO_AUTO_PURCHASE_VALIDATION: bool = False

    ## UPDATE THREAD
    DELTA_SEARCH_PURCHASE: List[int] = [0, 1, 0, 0]  # YEAR, MONTH, WEEK, DAY
    BUILD_UPDATE_TIME: List[int] = [23, 59, 50]  # daily, TIME THREAD IS STARTED

    ## BACKUP THREAD
    BUILD_ON_BACKUP: bool = False
    BACKUP_FREQUENCY: List[int] = [0, 3, 0, 0]  # DAY, HOURS, MINUTES, SECONDES

    ## WRITE LOG
    LOGGER_WRITE_ERROR: bool = True

    # CAMERA
    CAMERA_FRAME_WIDTH: int = 300
    CAMERA_FRAME_HEIGHT: int = 200
    CAMERA_FPS: int = 120
    CAMERA_PKG_FREQUENCY: int = 2  # 0 == all frames are transfered to the server.
    # scale on FPS AS: cameraFPS / cameraPackageFrequency == number of package sent per second.
    # setting 120FPS / 1 CPF + 1,
    # result on a constant package transfert every 0.15 sec
    # ( 6~7 frame per second received by the server)


class StagingConfig(Config):
    # FLASK
    ENV: str = "development"
    DEBUG: bool = True
    TESTING: bool = True
    TEMPLATES_AUTO_RELOAD: bool = True

    # FLASK-SOCKETIO
    ENGINEIO_LOGGER: bool = True
    LOGGER: bool = True

    # ERPPEEK API
    # ADDRESS: str = 'http://localhost:5000'
    # API_URL: str = 'https://superquinquin.staging.foodcoop12.trobz.com'
    # API_DB: str = 'superquinquin_staging'
    API_VERBOSE: bool = False

    ## POST OPTIONS
    ODOO_CREATE_NEW_PURCHASE_LINE: bool = True
    ODOO_AUTO_PURCHASE_VALIDATION: bool = False

    ## UPDATE THREAD
    DELTA_SEARCH_PURCHASE: List[int] = [0, 0, 7, 0]  # YEAR, MONTH, WEEK, DAY
    BUILD_UPDATE_TIME: List[int] = [23, 59, 50]  # daily, TIME THREAD IS STARTED

    ## BACKUP THREAD
    BUILD_ON_BACKUP: bool = False
    BACKUP_FREQUENCY: List[int] = [0, 3, 0, 0]  # DAY, HOURS, MINUTES, SECONDES

    ## WRITE LOG
    LOGGER_WRITE_ERROR: bool = False

    # CAMERA
    CAMERA_FRAME_WIDTH: int = 300
    CAMERA_FRAME_HEIGHT: int = 200
    CAMERA_FPS: int = 120
    CAMERA_PKG_FREQUENCY: int = 2


class DevelopmentConfig(Config):
    # FLASK
    ENV: str = "development"
    DEBUG: bool = False
    TESTING: bool = False
    TEMPLATES_AUTO_RELOAD: bool = True

    # FLASK-SOCKETIO
    ENGINEIO_LOGGER: bool = False
    LOGGER: bool = True

    # ERPPEEK API
    ADDRESS: str = "http://localhost:5000"  # 127.0.0.1:5000     # LOCALHOST
    API_URL: str = "https://superquinquin.staging.foodcoop12.trobz.com"
    API_DB: str = "superquinquin_staging"
    API_VERBOSE: bool = False

    ## POST OPTIONS
    ODOO_CREATE_NEW_PURCHASE_LINE: bool = True
    ODOO_AUTO_PURCHASE_VALIDATION: bool = True

    ## UPDATE THREAD
    DELTA_SEARCH_PURCHASE: List[int] = [0, 0, 0, 3]  # YEAR, MONTH, WEEK, DAY
    BUILD_UPDATE_TIME: List[int] = [
        18,
        0,
        0,
    ]  #                # daily, TIME THREAD IS STARTED H,M,S

    ## BACKUP THREAD
    BUILD_ON_BACKUP: bool = True
    BACKUP_FREQUENCY: List[int] = [5, 10, 0, 0]  # DAY, HOURS, MINUTES, SECONDES

    ## WRITE LOG
    LOGGER_WRITE_ERROR: bool = False

    # CAMERA
    CAMERA_FRAME_WIDTH: int = 300
    CAMERA_FRAME_HEIGHT: int = 200
    CAMERA_FPS: int = 120
    CAMERA_PKG_FREQUENCY: int = 2


class ClientJsonConfig(object):
    @classmethod
    def _to_dict(
        self, config: object, subconfig: object
    ) -> Dict[str, Union[str, bool, int]]:
        """__dict__ is not serialisable. Can't be parsed as Json"""

        return dict(
            [
                (k, v)
                for k, v in list(config.__dict__.items())
                + list(subconfig.__dict__.items())
                if (
                    k.startswith("CAMERA")
                    or k.startswith("ADDRESS")
                    or k.startswith("COLOR")
                )
            ]
        )

    @classmethod
    def to_json(self, config: object, subconfig: object):
        """Build JSON client config"""

        with open(config.JSON_CONFIG_FILENAME, "w") as js:
            js.write("var config = ")
            json.dump(self._to_dict(config, subconfig), js)
            js.write(";")


configDict = {
    "production": ProductionConfig,
    "staging": StagingConfig,
    "dev": DevelopmentConfig,
}


def parser():
    parser = argparse.ArgumentParser(description="choose config")
    parser.add_argument(
        "--config",
        choices=["dev", "staging", "production"],
        help="add config setup dev, staging or production",
    )
    args = parser.parse_args()

    return args


def define_config(config_name: Union[None, str] = None):
    if config_name is None:
        config_name = environ.get("APP_CONFIG", "dev")

    config = configDict[config_name]

    return config


def define_client_config(config):
    ClientJsonConfig.to_json(config=Config, subconfig=config)
