from typing import Any, Dict, Optional

import PIL  # noqa: F401
import qrcode

from cannettes_v2.models.room import Room
from cannettes_v2.utils import is_too_old

Payload = Dict[str, Any]


class Lobby(object):
    def __init__(
        self,
        *,
        rooms: Dict[str, Room] = {},
    ) -> None:
        self.rooms = rooms

    def generate_room_rid(self) -> int:
        rid = 0
        existing_rids = list(self.rooms.keys())
        if existing_rids:
            rid = max(existing_rids) + 1
        return rid

    def room_factory(self, context: Payload) -> Room:
        rid = self.generate_room_rid()
        room = Room(rid=rid, **context)
        room.data.is_starting()
        self.rooms[rid] = room
        return room

    def reset_room(self, room_id: str) -> None:
        room = self.rooms.get(room_id)
        room.data.build_registeries()

    def delete_room(self, room_id: str) -> None:
        self.rooms.pop(room_id)

    def find_room_associated_to_purchase(self, oid: int) -> Optional[Room]:
        for room in self.rooms:
            if room.data.oid == oid:
                return room.data.rid

    def assembling_rooms(self, room_id: int, other_room_id: int) -> Room:
        r1 = self.rooms.get(room_id)
        r2 = self.rooms.get(other_room_id)
        r1.data.assembler(r2.data)
        r1.name = f"{r1.name} (assemblés)"
        self.rooms.pop(other_room_id)
        return r1

    def finishing_room(self, room_id: int) -> None:
        self.rooms.get(room_id).is_finished()

    def validating_room(self, room_id: int) -> None:
        self.rooms.get(room_id).is_validated()

    def qrcode_iterator(self, context: Payload) -> Payload:
        payload = {"qrcodes": []}
        origin = context["origin"]
        for rid in context["room_ids"]:
            room = self.rooms.get(rid)
            caption = {"id": room.data.name, "supplier": room.data.supplier.name}
            qrcode = self._generate_qrcode(origin, room)
            payload["qrcodes"].append(zip(qrcode, caption))
        return payload

    def remove_associated_room(self, oid: int) -> None:
        for rid, room in self.rooms.items():
            if room.data.oid == oid:
                self.rooms.pop(rid)
                break

    def remove_outdated_rooms(self):
        for rid, room in self.rooms.items():
            _state = room.state.current()
            if _state == "done" and is_too_old(room.closing_date, 604800):
                self.rooms.pop(rid)

    def _generate_qrcode(self, origin: str, room: Room):
        link = f"{origin}/lobby/room?id={str(room.id)}&type={room.type}"
        qrc = qrcode.make(link).convert("RGB")
        return qrc
