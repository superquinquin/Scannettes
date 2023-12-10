import re
import time
from erppeek import Client, Record
from typing import Dict, List, Tuple, Union, Any

from cannettes_v2.utils import get_best_state

class Odoo(object):
    connected = False
    
    def connect(
        self,
        url: str,
        username: str,
        password: str,
        db: str,
        verbose: bool,
        max_retries: int=5,
        **kwargs
    ) -> None:
        
        tries = 0
        while self.connected is False:
            if tries > max_retries:
                self.connected = False
                raise RuntimeError("enable to connect to Odoo.") # Future exception
            
            try:
                self.client = Client(url, verbose=verbose)
                self.log = self.client.login(username, password=password, database=db)
                self.user = self.client.ResUsers.browse(self.log)
                self.tz = self.user.tz
                self.connected = True
                
            except Exception as e:
                print(e)
                tries += 1
                time.sleep(60)

    def get(self, model: str, cond: List[Tuple[str]]):
        """short for odoo client get method"""
        result = self.client.model(model).get(cond)
        return result

    def browse(self, model: str, cond: List[Tuple[str]]):
        """short for odoo client browse method"""
        result = self.client.model(model).browse(cond)
        return result

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
        if irt:
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
            print(items)
            item_state = get_best_state(items)
        return item_state


    def prepare_product_from_record(self, product: Record, **kwargs) -> Dict[str, Any]:
        """from product.product and external to the purchase"""
        payload = {
            "pid": product.id,
            "name": re.sub("\[.*?\]", "", self.get_name_translation(product)),
            "barcodes": self.get_barcodes(product),
            "qty": 0,
            "qty_virtual": 0,
            "qty_package": 0,
        }
        payload.update(kwargs)
        return payload