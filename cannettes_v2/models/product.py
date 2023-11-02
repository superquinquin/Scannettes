from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from cannettes_v2.models.state_handler import State, PRODUCT_STATE
from cannettes_v2.utils import generate_uuid

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
    qty: int = field(compare=False, default=0)
    qty_virtual: int =  field(compare=False, default=0)
    qty_package: int =  field(compare=False, default=0)
    qty_received: int =  field(compare=False, default=0)
    uomid: int = field(compare=True, default=None)
    state: State = field(compare=False, default=State(PRODUCT_STATE))
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
        qty: int = 0,
        qty_virtual: int = 0,
        qty_package: int = 0,
        uomid: Optional[int] = None,
        state: State = State(PRODUCT_STATE),
        _modified: bool = False,
        _scanned: bool = False,
        _new: bool = False,
        _unknown: bool = False,
        **kwargs,
    ) -> None:
        
        self.pid = pid
        self.name = name
        self.barcodes = barcodes
        self.qty = int(qty)
        self.qty_virtual = int(qty_virtual)
        self.qty_package = int(qty_package)
        self.uomid = uomid
        self.state = state
        self._modified = _modified
        self._scanned = _scanned
        self._new = _new
        self._unknown = _unknown
        
        self.uuid = generate_uuid()
        self.qty_received = self.qty
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
        for k, v in payload.items():
            current = getattr(self, k, None)
            if current is None:
                raise KeyError(f"{self} : {k} attribute doesn't exist")
            if type(current) != type(v) and current is not None:
                raise TypeError(
                    f"{self} : field {k} value {v} ({type(v)}) does not match current type : {type(current)}"
                )
            setattr(self, k, v)

    def to_payload(self, single_brcd: bool = False) -> Payload:
        payload = vars(self)
        if single_brcd:
            payload["barcodes"] = payload.get("barcodes")[0]
        return payload
