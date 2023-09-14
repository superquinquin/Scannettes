import qrcode
import PIL

from cannettes_v2.models.user import User
from cannettes_v2.models.room import Room
from cannettes_v2.utils import is_too_old


class Lobby:
    def __init__(self):
        pass

    # Lobby Rooms
    def create_room(self, input: dict, data: dict) -> Room:
        """add a room into lobby
        room is stored into cache['lobby']['rooms'][id]"""
        id = input["id"]
        data["lobby"]["rooms"][id] = Room(
            input["id"],
            input["name"],
            input["password"],
            input["object_id"],
            input["object_type"],
            data,
        )
        return data["lobby"]["rooms"][id]

    def room_assembler(self, r1: Room, r2: Room) -> Room:
        """merge 2 rooms data into one room: r1
        Delete room2 in the process

        Args:
            r1 (Room): Inventory Stock room
            r2 (Room): Inventory rayon room

        Returns:
            Room: newly merged room
        """
        r1_inv = r1.purchase
        r2_inv = r2.purchase
        r1_inv.assembler(r2_inv)
        r1.name = "assemblés"
        return r1

    def reset_room(self, id: str, data: dict):
        """return room and linked object into it's original state
        empty all subrpocess table entries, queue and done,
        replace entries table by the origin table"""
        data["lobby"]["rooms"][id].purchase.build_process_tables()

    def delete_room(self, id: str, data: dict):
        """delete a selected room from cache['lobby']['rooms']"""
        data["lobby"]["rooms"].pop(id)

    # Lobby Users
    def create_user(self, context: dict, data: dict) -> None:
        """create an admin user,
        store the user in cache['lobby']['users'][id]"""
        id = context["id"]
        data["lobby"]["users"][id] = User(
            context["ip"], context["id"], context["location"], context["admin"]
        )

    def move_user(self, id, move, data):
        data["lobby"]["users"][id].location = move

    def delete_user(self, id, data):
        data["lobby"]["users"].pop(id)

    def get_user_permissions(self, context: dict, data: dict) -> dict:
        """takes users input and match it with admin database
        GRANT ADMIN ACCESS ON MATCH"""
        id = context["id"]
        password = context["password"]
        whitelist = open(
            data["config"].WHITELIST_FILENAME, "r", encoding="utf-8", errors="ignore"
        )
        for identifier in whitelist.readlines():
            i = identifier.split()
            if id == i[0] and password == i[1]:
                context["permission"] = True
                data["lobby"]["users"]["admin"][id] = User(
                    id, "lobby", context["browser"], context["permission"]
                )
                context["token"] = data["lobby"]["users"]["admin"][id].token
                break

        return context

    #############################################################################
    ##################### QRCODE ################################################

    def generate_qrcode(self, origin: str, room: object):
        """CREATE QRCODE IMAGE FOR A GIVEN URL

        Args:
            origin (str): page origin
            room (object): room to pass as url

        Returns:
            PIL: PIL image
        """
        link = (
            f"{origin}/lobby/{room.id}%26type%3D{room.type}%26roomtoken%3D{room.token}"
        )
        qrc = qrcode.make(link).convert("RGB")

        return qrc

    def qrcode_iterator(self, context: dict, data: dict) -> dict:
        """TAKES SELECTED ROOM AND BUILD SET OF QRCODE IMAGES AND RELATED CAPTIONS

        Args:
            context (dict): url parts and rooms id to access
            data (dict): cache for accessing room data

        Returns:
            dict: list of qrcode and relatedcaptions
        """
        qrcode_list, room_caption = [], []

        origin = context["origin"]
        for id in context["room_ids"]:
            room = data["lobby"]["rooms"][id]
            room_caption.append(
                {"id": room.purchase.name, "supplier": room.purchase.supplier.name}
            )
            qrcode_list.append(self.generate_qrcode(origin, room))

        return {"qrcodes": qrcode_list, "captions": room_caption}

    #############################################################################
    ##################### update ROOM ###########################################

    def update_room_associated_to_purchase(
        self, data: dict, purchase_id: int, status: str
    ) -> bool:
        """original method updating room status when purchase is done"""
        updated = False
        rooms = list(data["lobby"]["rooms"].keys())

        for key in rooms:
            room = data["lobby"]["rooms"][key]
            room_purchase_id = room.purchase.id
            if room_purchase_id == purchase_id:
                updated = True
                room.change_status(status)

        return updated

    def force_room_status_update(self, data: dict) -> dict:
        """prevent room to exist unlimitedly
        if its linked purchase somehow got validated from a side way
        force status to go into done,
        so room and purchase will ultimately be cleared from cache"""
        rooms = list(data["lobby"]["rooms"].keys())
        done = list(data["odoo"]["purchases"]["done"].keys())

        for k in rooms:
            room = data["lobby"]["rooms"][k]
            status = room.status
            purchase_id = room.purchase.id

            if purchase_id in done and status != "done":
                room.change_status("done")

        return data

    #############################################################################
    ##################### REMOVE ROOM ###########################################

    def remove_room_associated_to_purchase(self, data: dict, purchase_id: int) -> None:
        """search room associated to a purchase. if delete = true, fully delete room
          else move it to done.

        Args:
            purchase_id (int): id of the purchase we are looking at.
            purchase_id (Dict): Data dict.
        """
        rooms = list(data["lobby"]["rooms"].keys())

        for key in rooms:
            room = data["lobby"]["rooms"][key]
            room_id = room.id
            room_purchase_id = room.purchase.id
            if room_purchase_id == purchase_id:
                self.delete_room(room_id, data)

    def remove_historic_room(self, odoo: object, data: dict) -> dict:
        """REMOVE ROOM AND PURCHASE FROM CACHE WHEN IT HAS BEEN CLOSED FOR
        A CERTAIN AMOUNT OF TIME in sec

        Args:
            odoo (object): _description_
            data (dict): _description_

        Returns:
            dict: updated cache data dict
        """
        keys = list(data["lobby"]["rooms"].keys())
        for k in keys:
            room = data["lobby"]["rooms"][k]
            room_id = room.id
            room_status = room.status
            purchase_id = room.purchase.id
            purchase_type = room.purchase.pType
            closing_date = room.closing_date
            if room_status == "done" and is_too_old(closing_date, 604800):
                self.delete_room(room_id, data)
                odoo.delete_purchase(purchase_id, data, purchase_type, "done")

        return data
