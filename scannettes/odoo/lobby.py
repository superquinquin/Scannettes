from copy import deepcopy
from collections import ChainMap
from typing import Any, Dict, Tuple, List, Type, Optional

import PIL  # noqa: F401
from PIL import Image
import qrcode

from scannettes.models.room import Room
from scannettes.tools.utils import is_too_old

Payload = Dict[str, Any]


class Lobby(object):
    def __init__(
        self,
        *,
        rooms: Dict[str, Room] = {},
    ) -> None:
        self.rooms = rooms
        

    def as_backup(self) -> Payload:
        return {"rooms": self.rooms}

    def get_open_rooms(self) -> List[Room]:
        return [room for room in self.rooms.values() if room.state.current() == "open"]
    
    def get_all_rooms(self) -> List[Room]:
        return [room for room in self.rooms.values()]

    def generate_room_rid(self) -> int:
        rid = 0
        existing_rids = list(self.rooms.keys())
        if existing_rids:
            rid = max(existing_rids) + 1
        return rid

    def room_factory(self, context: Payload) -> Room:
        rid = self.generate_room_rid()
        room = Room(rid=rid, **context)
        room.data.associated_rid = rid
        if room.data.process_state.is_passed("started") is False: # -------- MAKE IT BETTER
            room.data.is_starting()
        self.rooms[rid] = room
        return room

    def room_sibling_factory(self, context: Payload, inv1: type, inv2: type) -> Tuple[Room, Room]:
        shelf_payload = ChainMap(deepcopy(context), {"data": inv1})
        stock_payload = ChainMap(deepcopy(context), {"data": inv2})
        shelf_payload["name"] = f"Rayons {context['name']}"
        stock_payload["name"] = f"Stock {context['name']}"
        shelf_room = self.room_factory(shelf_payload)
        stock_room = self.room_factory(stock_payload)
        shelf_room.sibling = stock_room.rid
        stock_room.sibling = shelf_room.rid
        return (shelf_room, stock_room)
        
    def reset_room(self, rid: str) -> None:
        room = self.rooms.get(rid)
        process_state = room.data.process_state.current()
        if room.data.process_state.is_passed("started") and process_state != "started":  # ------- MAKE IT BETTER
            room.data.process_state.rollback_to("started")
        room.data.build_registeries()

    def delete_room(self, rid: str, inventories: Optional[Type]=None) -> None:
        room = self.rooms.pop(rid)
        room.data.associated_rid = None
        if room.sibling:
            other_rid = room.sibling
            self.rooms.get(other_rid).sibling = None
        if room.type == "inventory" and inventories:
            oid = room.data.oid
            inventories.inventories.pop(int(oid), None)
            
    
    
    def can_assemble(self, rid: int, other_rid: int) -> bool:
        state = self.rooms.get(rid).state.current() == "close"
        other_state = self.rooms.get(other_rid).state.current() == "close"
        return all([state, other_state])

    def assembling_rooms(self, rid: int, other_rid: int) -> Optional[Room]:
        r1 = self.rooms.get(rid)
        r2 = self.rooms.get(other_rid)
        r1.data.assembler(r2.data)
        r1.name = f"{r1.name} (assemblés)"
        self.rooms.pop(other_rid)
        return r1

    def finishing_room(self, rid: int) -> None:
        self.rooms.get(rid).is_finished()

    def validating_room(self, rid: int) -> None:
        self.rooms.get(rid).is_validated()

    def qrcode_iterator(self, context: Payload) -> Payload:
        payload = {"qrcodes": []}
        origin = context["origin"]
        for rid in context["rids"]:
            room = self.rooms.get(rid)
            caption = {"id": room.data.name, "supplier": room.data.supplier.name}
            qrcode = self._generate_qrcode(origin, room)
            payload["qrcodes"].append((qrcode, caption))
        return payload

    def remove_associated_room(self, oid: int) -> None:
        for rid, room in self.rooms.items():
            if room.data.oid == oid:
                self.rooms.pop(rid)
                break

    def remove_outdated_rooms(self, max_age: int, inventories: object) -> None:
        """
        room & purchase/inventory removing process
        purchase -> removed by update thread. rooms must be non displayable when room gets to old.
        inventory -> removing when too old. remove room and inventory at same time.
        """
        for rid, room in deepcopy(self.rooms).items():
            _state, _type = room.state.current(), room.type
            if _state == "done" and _type == "purchase" and is_too_old(room.closing_date, max_age):
                self.rooms.pop(rid)
            elif _state == "done" and _type == "inventory" and is_too_old(room.closing_date, max_age):
                oid = room.data.oid
                inventories.inventories.pop(oid)
                self.rooms.pop(rid)

    def _generate_qrcode(self, origin: str, room: Room) -> Image:
        link = f"{origin}/lobby/room/{room.token}?rid={str(room.rid)}&type={room.type}"
        qrc = qrcode.make(link).convert("RGB")
        return qrc
