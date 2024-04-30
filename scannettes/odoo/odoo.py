from __future__ import annotations

import re
import time
from erppeek import Client, Record
from typing import Dict, List, Tuple, Union, Any
from functools import wraps
from http.client import CannotSendRequest
import http.client as hc

from scannettes.tools.utils import get_best_state

class Odoo(object):
    connected: bool = False
    
    def __init__(self, creds) -> None:
        self.creds = creds
        
    def connect(
        self,
        url: str,
        username: str,
        password: str,
        db: str,
        verbose: bool,
        max_retries: int=5
        ) -> None:
        _conn, _tries = False, 0
        while (_conn is False and _tries <= max_retries):
            try:
                self.client = Client(url, verbose=verbose)
                self.log = self.client.login(username, password=password, database=db)
                self.user = self.client.ResUsers.browse(self.log)
                self.tz = self.user.tz
                _conn = True
            except Exception:
                time.sleep(5)
                _tries += 1
        
        if _conn is False:
            raise ConnectionError("enable to connect to Odoo.")
    
    def _refresher(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            self = args[0]
            _ok, _tries, _max_tries = False, 0, 3
            while _tries <= _max_tries and _ok is False:                
                try:
                    res = f(*args, **kwargs)
                    _ok = True
                except (CannotSendRequest, AssertionError):
                    _tries += 1
                    self.connect(**self.creds)
            if _ok is False:
                raise ConnectionError("cannot connect to odoo")
            return res
        return wrapper
        
    @_refresher
    def get(self, model: str, cond: List[Tuple[str]]):
        """short for odoo client get method"""
        result = self.client.model(model).get(cond)
        return result

    @_refresher
    def browse(self, model: str, cond: List[Tuple[str]]):
        """short for odoo client browse method"""
        result = self.client.model(model).browse(cond)
        return result

    @_refresher
    def create(self, model: str, object: Dict[str, Any]):
        """short for odoo client create method"""
        result = self.client.model(model).create(object)
        return result

    def apply_purchase_record_change(self, move_id: int, received_qty: int):
        """during post purchase process update odoo record value"""
        move = self.get("stock.move.line", [("move_id.id", "=", move_id)])
        move.qty_done = received_qty
    
    def get_barcodes(self, product: Record) -> Union[List[int], List[bool]]:
        """collect all barcodes for a PP record"""
        main = product.barcode
        alt = self.browse(
            "product.multi.barcode",
            [("product_id", "=", product.id)]
        ).barcode
        barcodes = [main] + alt
        return barcodes
    
    def search_product_from_barcode(self, barcode: str) -> Record:
        return self.get("product.product", [("barcode", "=", barcode)])
    
    def get_name_translation(self, pt: Record) -> str:
        """get PT name or IR translation if any"""
        name = pt.name
        irt = self.browse("ir.translation", [("res_id", "=", pt.id), ("name", "=", "product.template,name")])
        if irt and irt[0].value != "":
            name = irt[0].value
        return name.strip()
    
    def get_picking_state(self, name: str) -> str:
        """Search for purchase picking state
        :states: None < Cancel < assigned < done
        """
        try:
            picking_state = "draft"
            picking = self.get("stock.picking", [("origin", "=", name)])
            if picking:
                picking_state = picking.state
                
        except ValueError:
            picking = self.browse("stock.picking", [("origin", "=", name)]).state
            picking_state = get_best_state(picking)
        return picking_state

    def get_item_state(self, name: str, id: int) -> str:
        """Search for item state in a purchase
        :states: None < Cancel < assigned < done
        """
        try:
            item_state = "none"
            item = self.get(
                "stock.move", [("origin", "=", name), ("product_id.id", "=", id)]
            )
            if item:
                item_state = item.state

        except ValueError:
            items = self.browse(
                "stock.move", [("origin", "=", name), ("product_id.id", "=", id)]
            ).state
            item_state = get_best_state(items)
        return item_state

    def prepare_product_from_record(self, product: Record, **kwargs) -> Dict[str, Any]:
        """from product.product and external to the purchase"""
        pt = product.product_tmpl_id
        payload = {
            "pid": product.id,
            "name": re.sub("\[.*?\]", "", self.get_name_translation(pt)),
            "barcodes": self.get_barcodes(product),
            "qty": float(0),
            "qty_virtual": float(pt.qty_available),
            "qty_package": float(0),
            "uomid": pt.uom_id.id
        }
        payload.update(kwargs)
        return payload