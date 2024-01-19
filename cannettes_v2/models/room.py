import base64
import numpy as np
from datetime import datetime
from pyzbar.pyzbar import decode
from itertools import chain
from typing import Any, Dict, Literal, Optional, Union

from cannettes_v2.models.purchase import Inventory, Purchase
from cannettes_v2.models.state_handler import RoomState, State
from cannettes_v2.odoo.odoo import Odoo
from cannettes_v2.utils import generate_uuid, update_object, restrfmtdate

Payload = Dict[str, Any]
RoomType = Literal["purchase", "inventory"]
SearchType = Literal["image", "laser"]


class Room(object):
    def __init__(
        self,
        *,
        rid: int,
        name: str = "",
        password: Optional[str] = None,
        type: RoomType,
        sibling: Optional[int] = None,
        data: Union[Purchase, Inventory],
        state: Optional[State] = None,
        **kwargs,
    ) -> None:
        self.rid = rid
        self.name = name
        self.password = password
        self.type = type
        self.sibling = sibling
        self.data = data
        self.state = state or State(RoomState)
        self.closing_date = None
        self.creating_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.token = generate_uuid()
        self.__dict__.update(**kwargs)

        self._image_handler = [
            self._image_decoder,
            self._is_not_scanned_yet,
            self.data.search_scanned_in_self,
            self.data.search_scanned_in_odoo,
            self.data.build_external_product
        ]

        self._laser_handler = [
            self._is_not_scanned_yet,
            self.data.search_scanned_in_self,
            self.data.search_scanned_in_odoo,
            self.data.build_external_product
        ]

    def __repr__(self) -> str:
        return f"<{self.rid} {self.name} ({self.type}) : {self.state}>"

    def update(self, payload: Payload) -> None:
        update_object(self, payload)

    def is_finished(self):
        self.state.bump_to("close")
        self.data.is_finished()

    def is_validated(self):
        self.closing_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.state.bump_to("done")
        self.data.is_validated()

    def search_product(
        self,
        stype: SearchType,
        context: Payload,
        api: Odoo,
    ) -> Payload:
        
        context.update({"flag": True})
        handlers = iter(getattr(self, f"_{stype}_handler"))
        while context["flag"]:
            handler = next(handlers)
            context = handler(context=context, api=api)
        if context.pop("external", False):
            self.data.add_product(context["res"]["product"])
        return context

    def _decoder(self, context: Payload, **kwargs) -> np.ndarray:
        """base64 strings decode it into numpy array of shape [n,m,1]"""
        fh, fw = context["fh"], context["fw"]
        bytes = base64.b64decode(context["data"])
        pixels = np.array([b for b in bytes], dtype="uint8")
        return np.array(pixels).reshape(fh, fw).astype("uint8")

    def _image_decoder(self, context: Payload, **kwargs) -> Payload:
        image = self._decoder(context)
        barcode = decode(image)
        if barcode:
            context["barcode"] = barcode[0].data.decode("utf-8")
        else:
            context["res"] = {"msg": ""}
        return context

    def _is_not_scanned_yet(self, context: Payload, **kwargs) -> Payload:
        """payload : {"barcode"(str), "flag"(bool) res(payload)}"""
        if context["barcode"] in list(chain.from_iterable([p.barcodes for p in self.data.get_scanned_products()])):
            context["flag"] = False
            context["res"] = {"scanned": True}
        return context

    
    def to_payload(self) -> Payload:
        return {
            "rid": self.rid,
            "name": self.name,
            "type": self.type,
            "token": self.token,
            "state": self.state.current(),
            "sibling": self.sibling,
            "creating_date": restrfmtdate(self.data.create_date) or restrfmtdate(self.creating_date),
            "oid": self.data.oid,
            "display_name": self.data.display_name(),
            "supplier": self.data.supplier.name if self.type == "purchase" else None
        }