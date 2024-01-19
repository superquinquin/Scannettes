from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from cannettes_v2.models.state_handler import State, ProductState
from cannettes_v2.utils import generate_uuid, update_object

Payload = Dict[str, Any]



@dataclass(init=False, repr=False, eq=True)
class Product(object):
    """
    Base Product Dataclass.
    Minimalistic representation of Odoo or external products.
    
    Class Equality comparison based attributes:
        (pid, name, barcodes, uomid)
        
    Class ordering based on Names
    
    Attr:
        :uuid: (str) unique internal identifier. Handy for retrieving product as they are more reliable than pid, barcodes and names.
        :pid: (int) Odoo product.product id.
        :name: (str) Odoo product.product name.
        :barcode: (int) Odoo product.product barcode.
        :qty: (int) Purchased quantity.
        :qty_virtual: (int) quantity theorically in stock if we omit stock errors
        :qty_package: (int) quantity of purchased package. (qty_pkg * pkg_size = qty)
        :qty_received: (int) quantity really received or in stock. 
        :state: (str) Current state of the product. Default : "initial". the state can move from "initial" to "queue" then to "done".
        :_modified: (bool) True when a product qty has been modified.
        :_scanned: (bool) True when the product has been scanned inside a room
        :_new: (bool) True when the product doesn't originate from the base template
        :_unknown: (bool) True when no reference are found in Odoo. 
    """    

    pid: Optional[int] = field(compare=True, default=None)
    uuid: str = field(compare= False)
    name: str = field(compare=True, default="")
    barcodes: List[Union[str, bool]] = field(compare=True)
    qty: float = field(compare=False, default=float(0))
    qty_virtual: float = field(compare=False, default=float(0))
    qty_package: float = field(compare=False, default=float(0))
    qty_received: float = field(compare=False, default=float(0))
    uomid: int = field(compare=True, default=None)
    state: State = field(compare=False, default=None)
    _modified: bool = field(compare=False, default=False),
    _scanned: bool = field(compare=False, default=False),
    _new: bool = field(compare=False, default=False),
    _unknown: bool = field(compare=False, default=False),

    def __init__(
        self,
        *,
        pid: Optional[int] = None,
        name: str = "",
        barcodes: List[Union[str, bool]],
        qty: float = float(0),
        qty_virtual: float = float(0),
        qty_package: float = float(0),
        uomid: Optional[int] = None,
        state: Optional[State] = None,
        _modified: bool = False,
        _scanned: bool = False,
        _new: bool = False,
        _unknown: bool = False,
        **kwargs,
    ) -> None:
        
        self.pid = pid
        self.name = name
        self.barcodes = barcodes
        self.qty = float(qty)
        self.qty_virtual = float(qty_virtual)
        self.qty_package = float(qty_package)
        self.uomid = uomid
        self.state = state or State(ProductState)
        self._modified = _modified
        self._scanned = _scanned
        self._new = _new
        self._unknown = _unknown
        
        self.uuid = generate_uuid()
        self.qty_received = float(0)
        self.__dict__.update(**kwargs)

    def __repr__(self) -> str:
        return f"<{self.uuid} - {self.name}({str(self.pid)})>"
    
    def __lt__(self, other: Product) -> bool:
        return self.name < other.name
        
    def __gt__(self, other: Product) -> bool:
        return self.name > other.name
    
    def __le__(self, other: Product) -> bool:
        return self.name <= other.name
    
    def __ge__(self, other: Product) -> bool:
        return self.name >= other.name

    def update(self, payload: Payload) -> None:
        update_object(self, payload)

    def status_quo(self) -> None:
        self.qty_received = self.qty
        
    def modify(self, wmod: bool=False, modifications: Dict[str, Any]= {}):
        if self.state.current() != "done":
            self._scanned = True
            self.state.bump_to("done")
        if wmod:
            self._modified = True
            self.update(modifications)


    def to_payload(self, single_brcd: bool = False) -> Payload:
        payload = {
            "pid": self.pid,
            "name": self.name,
            "barcodes": self.barcodes,
            "qty": self.qty,
            "qty_virtual": self.qty_virtual,
            "qty_package": self.qty_package,
            "qty_received": self.qty_received,
            "uomid": self.uomid,
            "state": self.state.current(),
            "_modified": self._modified,
            "_scanned": self._scanned,
            "_new": self._new,
            "_unknown": self._unknown,
            "uuid": self.uuid,
        }
        if single_brcd:
            payload["barcodes"] = self.barcodes[0]
        return payload

    def as_inventory_payload(self, oid:int, location: int= 12) -> Payload:
        return {
            "product_qty": self.qty_received,
            "product_id": self.pid,
            "product_uom_id": self.uomid,
            "location_id": location,
            "inventory_id": oid,
        }

    def as_purchase_payload(self, oid: int, price: int, name: str) -> Payload:
        return {
            "order_id": oid,
            "product_uom": self.uomid,
            "price_unit": price,
            "product_qty": 1,
            "name": name,
            "product_id": self.pid,
            "date_planned": datetime.now(),
        }

    def fmt_display_name(self) -> str:
        if self.name == "":
            return f"{self.barcode} (nom absent)"
        elif self.barcodes == [False]:
            return f"{self.name} (code-barres absent)"
        else:
            return f"{self.name} ({self.barcodes})"