import base64
import numpy as np
import pandas as pd
from datetime import datetime
from pyzbar.pyzbar import decode

from cannettes.packages.purchase import Purchase
from cannettes.packages.utils import generate_token, get_status_related_collections


class Room:
    """ROOM INSTANCE

    ROOM IDENTIFIER
    @id (str): UNIQUE id for representing the room,
               used to store object inside cache as follow
               cache['lobby']['rooms'][id]
    @name (str): name give to the room, inpu from the user.
                 replaced by the id in case no name are given
    @token (str): UNIQUE HEX token used to build room url
    @password (str): password input from the user, optional
    @user (int): user count, UNUSED

    OBJECT
    @purchase (class:Purchase): linked INVENTORY or PURCHASE

    STATUS
    @type (str): can be [purchase, inventory], label the type of the object
    @status (str): can be [open, close, done], label the process status of the room and its related object
                   open: when the room is accessible for everyone, the object is still not processed or currently is
                   close: room restrained only to administrators, await for its object to be verified and validated
                   done: room restrained only to administrators, still visible but can't be interected with

    DATETIME
    @opening_date (str): date of creation of the room.
    @closing_date (str): date the room passed in 'done' status

    """

    def __init__(self, id, name, password, object_id, type, data):
        # status
        self.id = id
        self.name = name
        self.password = password
        self.token = generate_token(10)
        self.type = type
        self.status = "open"
        self.oppening_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.closing_date = None
        self.users = 0

        if not object_id:
            self.purchase = self.generate_pseaudo_purchase(data, id)

        elif object_id and type == "inventory":
            self.purchase = data["odoo"]["inventory"]["ongoing"][object_id]

        elif object_id and type == "purchase":
            self.purchase = data["odoo"]["purchases"]["incoming"][object_id]

    def generate_pseaudo_purchase(self, data: dict, id: str) -> Purchase:
        """building a table not binded to an existing purchase
        Create an empty template

        Args:
            data (dict): cache dict
            id (_type_): id to be taken inside the cache

        Returns:
            Purchase: _description_
        """
        spo_id = "spo" + str(
            len(list(data["odoo"]["purchases"]["pseudo-purchase"].keys())) + 1
        )
        spo_supplier = None
        spo_realness = False
        spo_ptype = "purchase"
        spo_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        spo_status = "incoming"
        spo_table = pd.DataFrame(
            [], columns=["barcode", "id", "name", "qty", "pckg_qty", "qty_received"]
        )

        data["odoo"]["purchases"]["pseudo-purchase"][id] = Purchase(
            spo_id,
            spo_id,
            spo_supplier,
            spo_realness,
            spo_ptype,
            spo_date,
            spo_date,
            spo_status,
            spo_table,
        )

        return data["odoo"]["purchases"]["pseudo-purchase"][id]

    def image_decoder(
        self, imageData: str, room_id: str, room: object, odoo: object, data: dict
    ) -> dict:
        """
        state: 0 for no ean found; 1 for new ean ; 2 for ean already scanned
        """
        image = self.decoder(imageData, data)

        image = np.array(image)
        ean = decode(image)  # ZBAR
        if ean:
            code_ean = ean[0].data.decode("utf-8")

            if code_ean not in self.purchase.scanned_barcodes:
                self.purchase.append_scanned_items(code_ean)

                context = self.search_and_move_scanned_item(code_ean, odoo)
                context["room_id"] = room_id
                context["scanned"] = self.purchase.scanned_barcodes
                context["new"] = self.purchase.new_items
                context["mod"] = self.purchase.modified_items
                context["state"] = 1
                print(code_ean)

            else:
                context = {"state": 2}
                print(code_ean, "is already scanned")

        else:
            context = {"state": 0}

        return context

    def decoder(self, image_data: str, data: dict) -> np.ndarray:
        """base64 strings
        decode it into numpy array of shape [n,m,1]"""

        bytes = base64.b64decode(image_data)
        pixels = np.array([b for b in bytes], dtype="uint8")

        image = (
            np.array(pixels)
            .reshape(
                data["config"].CAMERA_FRAME_HEIGHT, data["config"].CAMERA_FRAME_WIDTH
            )
            .astype("uint8")
        )

        return image

    def laser_decoder(
        self,
        laserData,
        room_id: str,
        barcode: int,
        room: object,
        odoo: object,
        data: dict,
    ) -> dict:
        """
        state: 1 ok; state 2: already scanned
        """

        if barcode not in self.purchase.scanned_barcodes:
            self.purchase.append_scanned_items(barcode)

            context = self.search_and_move_scanned_item(barcode, odoo)
            context["room_id"] = room_id
            context["scanned"] = self.purchase.scanned_barcodes
            context["new"] = self.purchase.new_items
            context["mod"] = self.purchase.modified_items
            context["state"] = 1

        else:
            context = {"state": 2}
            print(barcode, "is already scanned")

        return context

    def search_and_move_scanned_item(self, code_ean: str, odoo: object) -> dict:
        """SEARCH FOR ANY GIVEN BARCODE IF IT EXIST IN:
        state 0: THE PURCHASE OBJECT TABLES
        state 1: HAS AN ALT BARCODE THAT EXIST IN OBJECT TABLE
        state 2: WHETER BARCODE OR ALT BARCODE EXIST IN ODOO BUT NOT IN OBJECT TABLE
        state 3: PRODUCT CAN'T BE FOUND EITHER IN OBJECT TABLE OR ODOO

        AFTER DEFINING THE STATE OF THE PRODUCT
        IT GET EITHER MOVED FROM ENTRIES TO QUEUE TABLE OR IS ADDED INTO THE TABLE DIRECTLY

        Args:
            odoo (Odoo): object to interact with odoo db
            code_ean (str): barcode

        Return : context with product data
        """
        context = {"code_ean": code_ean, "flag": True, "state": 0, "product": None}

        if context["flag"] and context["state"] == 0:
            ## SEARCH FORPRODUCT EXISTENCE IN PURCHASE OBJECT
            context = self.purchase._state_0_search(context)

        if context["flag"] and context["state"] == 1:
            ## SEARCH FOR ALT BARCODE EXISTENCE
            ## AND WETHER IT EXIST IN PURCHASE OBJECT OR NOT
            context = self.purchase._state_1_search(odoo, context)

        if context["flag"] and context["state"] == 2:
            ## LOOKING FOR PRODUCT EXISTENCE IN ODOO
            context = self.purchase._state_2_search(odoo, context)

        context = self.purchase._move_scanned_item(odoo, context)
        return context

    def update_status(
        self, new: str, new_pr: str, new_rm, object_type: str, data: dict
    ):
        """take a room and modify its status, process status and binded object status

        Args:
            new (str): new purchase status
            new_pr (str): new process status
            new_rm (str)
            object_type (str): type of the object: purchase or inventory
            data (str): data dict
        """
        object_id = self.purchase.id
        self.purchase.status = new
        self.purchase.process_status = new_pr
        self.status = new_rm

        if self.status == "done":
            self.closing_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        prv, nxt = get_status_related_collections(object_type, new_pr)
        if object_type == "purchase":
            data["odoo"]["purchases"][nxt][object_id] = self.purchase
            data["odoo"]["purchases"][prv].pop(object_id, None)
            data["odoo"]["purchases"]["incoming"].pop(object_id, None)  # in case

        else:
            data["odoo"]["inventory"][nxt][object_id] = self.purchase
            data["odoo"]["inventory"][prv].pop(object_id, None)

    def change_status(self, status: str):
        self.status = status

        if status == "done":
            self.closing_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
