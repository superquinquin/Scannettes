from typing import Any, Dict, List, Optional, Union

from cannettes_v2.models.state_handler import State
from cannettes_v2.utils import generate_uuid

Payload = Dict[str, Any]


class Product(object):
    """
    Attr:
        :uuid: (str) unique internal identifier. Handy for retrieving product as they are more reliable than pid, barcodes and names.
        :pid: (int) Odoo product.product id.
        :name: (str) Odoo product.product name.
        :barcode: (int) Odoo product.product barcode.
        :qty: (int)
        :qtyvirtual: (int)
        :qtypackage: (int)
        :qtyreceived: (int)
        :state: (str) Current state of the product. Default : "initial". the state can move from "initial" to "queue" then to "done".
        :modified: (bool) True when a product qty has been modified.
    """

    def __init__(
        self,
        *,
        pid: Optional[int] = None,
        name: str = "",
        barcodes: Union[List[int], List[bool]],
        qty: int = 0,
        qty_virtual: int = 0,
        qty_package: int = 0,
        state: State,
        _modified: bool = False,
        _scanned: bool = False,
        _new: bool = False,
        _unknown: bool = False,
        **kwargs,
    ) -> None:
        self.pid = pid
        self.name = name
        self.barcodes = barcodes
        self.qty = qty
        self.qty_virtual = qty_virtual
        self.qty_package = qty_package
        self.state = state
        self._modified = _modified
        self._scanned = _scanned
        self._new = _new
        self._unknown = _unknown
        self.uuid = generate_uuid()
        self.qty_received = self.qty
        self.__dict__.update(**kwargs)

    def __repr__(self) -> str:
        return f"<{self.uuid} - {str(self.pid)} {self.name}>"

    def update(self, payload: Payload) -> None:
        for k, v in payload.items():
            current = getattr(self, k, None)
            if current is None:
                raise KeyError(f"{self} : {k} attribute doesn't exist")
            if type(current) != type(v) and current is not None:
                raise TypeError(
                    f"{self} : field {k} value {v} ({type(v)}) does not match current type : {type(current)}"
                )
            setattr(self, k, v)

    def to_payload(self) -> Payload:
        return vars(self)
