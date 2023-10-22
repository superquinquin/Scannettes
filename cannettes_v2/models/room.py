import base64
from datetime import datetime
from typing import Any, Dict, Literal, Optional, Union

import numpy as np
from pyzbar.pyzbar import decode

# from cannettes_v2.models.product import Product
from cannettes_v2.models.purchase import Inventory, Purchase
from cannettes_v2.models.state_handler import ROOM_STATE, State
from cannettes_v2.odoo.deliveries import Deliveries
from cannettes_v2.odoo.inventories import Inventories
from cannettes_v2.odoo.odoo import Odoo
from cannettes_v2.utils import generate_uuid

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
        data: Union[Purchase, Inventory],
        creating_date: datetime,
        **kwargs,
    ) -> None:
        self.rid = rid
        self.name = name
        self.password = password
        self.type = type
        self.data = data
        self.creating_date = creating_date
        self.closing_date = None
        self.state = State(ROOM_STATE)
        self.token = generate_uuid()
        self.__dict__.update(**kwargs)

        self._image_handler = [
            self._image_decoder,
            self._is_not_scanned_yet,
            self.data.search_scanned_in_self,
            self.data.search_scanned_in_odoo,
            self.data.add_external_product,
            self.data.update_scanned_product,
        ]

        self._laser_handler = [
            self._is_not_scanned_yet,
            self.data.search_scanned_in_self,
            self.data.search_scanned_in_odoo,
            self.data.add_external_product,
            self.data.update_scanned_product,
        ]

    def __repr__(self) -> str:
        return f"<{self.rid} {self.name} ({self.type}) : {self._state}>"

    def update(self, payload: Payload) -> None:
        for k, v in payload.items():
            current = getattr(self, k, None)
            if current is None:
                raise KeyError(f"{self} : {k} attribute doesn't exist")
            if type(current) != type(v) and current is not None:
                raise TypeError(
                    f"{self} : field {k} value {v} ({type(v)}) does not match current type ({type(current)})"
                )
            setattr(self, k, v)

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
        api: Union[Odoo, Deliveries, Inventories],
    ) -> Payload:
        handlers = iter(getattr(self, f"_{stype}_handlers"))
        while context["res"] is None:
            handler = next(handlers)
            context = handler(context=context, api=api)
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
        if context["barcode"] in self.data.get_scanned_products():
            context["res"] = {"msg": ""}
        return context
