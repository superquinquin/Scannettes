import re
import time
from erppeek import Client, Record, RecordList
from typing import Dict, List, Tuple, Union, Any


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
                break
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
        
    def get_barcode(self, product: Record) -> int:
        """
        get barcode from multibarcode table
        handle False barcode from odoo
        """
        barcode = product.product_id.barcode
        alt = self.browse(
            "product.multi.barcode", [("product_id", "=", product.product_id.id)]
        )

        if barcode == False and alt:
            for p in alt:
                if p.barcode:
                    barcode = p.barcode
                    break
        return barcode
    
    def get_barcodes(self, product: Record) -> Union[List[int], List[bool]]:
        main = product.barcode
        alt = self.browse(
            "product.multi.barcode",
            [("product_id", "=", product.id)]
        )
        barcodes = [main] + alt.barcode
        return barcodes
        

    def search_product_from_barcode(self, barcode: str) -> Record:
        return self.get("product.product", [("barcode", "=", barcode)])
    
    
    def get_name_translation(self, pt: Record) -> str:
        name = pt.name
        irt = self.browse("ir.translation", [("res_id", "=", pt.id), ("name", "=", "product.template,name")])
        if irt:
            name = irt[0].value
        return name
    
    
    # def get_name_translation(self, product: Record) -> str:
    #     """
    #     search product translated name
    #     """
    #     name = None
    #     irt = self.browse(
    #         "ir.translation", [("res_id", "=", product.product_tmpl_id.id)]
    #     )
    #     for t in irt:
    #         if t.name == "product.template,name":
    #             name = t.value
    #             break
    #     if not name:
    #         name = product.name
    #     return name

    def get_picking_state(self, name: str) -> str:
        """try to search picking state of a purchase

        ON VALUE ERROR due to multiple picking id
        certainly from reediting purchase and cancel previous ones
        give priority as follow:
        None < Cancel < assigned < done

        Args:
            name (str): origin field in stock picking field

        Returns:
            str: current picking state, can be [None, 'cancel','assigned','done']
        """
        try:
            picking = self.get("stock.picking", [("origin", "=", name)])

            if picking:
                picking_state = picking.state

            else:
                picking_state = "draft"

        except ValueError as e:
            picking = self.browse("stock.picking", [("origin", "=", name)])
            picking_state = None

            for pick in picking:
                if pick.state == "cancel" and (
                    picking_state != "assigned" and picking_state != "done"
                ):  # set up to cancel
                    picking_state = pick.state

                elif (
                    pick.state == "assigned" and picking_state != "done"
                ):  # set up to assigned
                    picking_state = pick.state

                elif pick.state == "done":  # set up to done
                    picking_state = pick.state

        return picking_state

    def get_item_state(self, name: str, id: int) -> str:
        """try to search for item state

        ON VALUE ERROR
        can be due to multiple item with same id,
        originating from canceled item and reediting ones
        state priority : None < Cancel < assigned < done

        Args:
            name (str): origin field from stock.move
            id (int): product id

        Returns:
            str: item state, can be [None, 'cancel','assigned','done']
        """
        try:
            item = self.get(
                "stock.move", [("origin", "=", name), ("product_id.id", "=", id)]
            )
            if item:
                item_state = item.state

            else:
                item_state = "none"

        except ValueError as e:
            items = self.browse(
                "stock.move", [("origin", "=", name), ("product_id.id", "=", id)]
            )
            item_state = None

            for item in items:
                if item.state == "cancel" and (
                    item_state != "assigned" and item_state != "done"
                ):  # set up to cancel
                    item_state = item.state

                elif (
                    item.state == "assigned" and item_state != "done"
                ):  # set up to assigned
                    item_state = item.state

                elif item.state == "done":  # set up to done
                    item_state = item.state

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