import re
from erppeek import Record
from datetime import datetime
from typing import List, Dict, Tuple, Any, Optional

from cannettes_v2.odoo.odoo import Odoo
from cannettes_v2.models.purchase import Inventory
from cannettes_v2.models.product import Product

payload = Dict[str, Any]

class Inventories(Odoo):
    """
    main and only interaction between inventories and Odoo is done during exportation
    !! Odoo reference for inventories is obly created during exportation   !!
    !! For an inventory to be valid, please note that you shouldn't affect !!
    !! any of its product ouside of the inventory scope                    !!
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.categories: List[Tuple[str, int]]
        self.inventories: Dict[int, Optional[Inventory]] = {}
        self.last_update: datetime = None
        
        self.export_pipeline = [
            self._check_product_odoo_existence,
            self._create_stock_inventory_row,
            self._create_stock_inventory_line_row,
            self._propagate_start
        ]

    def build(self, erp: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        self.connect(**erp)
        return self.import_categories()

    def import_categories(self) -> None:
        cats = self.browse("product.category", [("create_date", ">", "1900-01-01 01:01:01")])
        self.categories = sorted(
            [(c.complete_name, c.id) for c in cats],
            key=lambda x: x[0],
            reverse=False,
        )

    def define_inventory_id(self) -> int:
        return max(self.inventories.keys()) + 1

    def inventory_factory(self, catid: int, name: str = "", **kwargs) -> Inventory:
        oid = self.define_inventory_id()
        inventory = Inventory(
            oid= oid,
            catid= catid,
            name= name,
            _initial_products= self.fetch_products(catid)
        )
        inventory.update(kwargs)
        self.inventories[oid] = inventory
        return inventory


    def fetch_products(self, catid: int) -> List[Product]:
        products = self.browse("product.template", [("categ_id", "=", catid), ("active", "=", True)])
        return [self.product_factory(product) for product in products]

    def product_factory(self, product: Record, **kwargs):
        name = self.get_name_translation(product.product_id.product_tmpl_id)
        prod = Product({
            "pid": product.product_id.id,
            "name": re.sub("\[.*?\]", "", name).strip(),
            "barcode": self.get_barcodes(product),
            "qty": product.product_qty,
            "qty_virtual": None,
            "qty_package": product.product_qty_package,
        })
        prod.update(kwargs)
        return prod


    def export_to_odoo(self, oid: int, autoval: bool= False) -> payload:
        """
        payload:
            :flag: stop process when raised
            :valid: track the process validity. Unvalid process must stop and hint the users about the problems
            :inventory: current app inventory object
            :container: the inventory reference newly created in Odoo. This very reference is going to be populated with the inventory products data.
            :failing: list of items failing the process
            :error_code: hint the error formating system
            
        process_steps:
            :_check_product_odoo_existence:
                verify that every product scanned by the app have an Odoo reference.
            :_create_stock_inventory_row:
                Try to create a stock.inventory reference
            :_create_stock_inventory_row:
                Try to populate the created reference with the scanned items
            :_propagate_start:
                Simulate inventory creation action on Odoo interface
            :_propagate_validate:
                deactivated by default. Validate automatically the created inventory.
                
        
        """
        payload = {"inventory":self.inventories.get(oid),"valid": True, "flag": True}
        handlers = iter(self.export_pipeline)
        while payload["flag"]:
            handler = next(handlers)  
            payload = handler(payload)
            if payload["valid"] is False:
                return payload
        self._propagate_validate(payload, autoval)
        return payload

        
    def _check_product_odoo_existence(self, payload: payload) -> payload:
        outsiders = payload["inventory"].get_unknown_products()
        payload.update({"valid": not any(outsiders), "failing": outsiders, "error_code": "odout"})
        return payload
        
    def _create_stock_inventory_row(self, payload: payload) -> payload:
        """create a 'stock.inventory' container to be filled with inventory lines"""
        date = datetime.now().strftime("%d-%m-%Y")
        name = f"{payload['inventory'].name} {date}"
        container = None
        try:
            container = self.create(
                "stock.inventory",
                {"name": name, "location_id": 12},
            )
        except Exception:
            payload.update({"valid": False, "container": None, "error_code":"odostockinvfail"})
        payload.update({"container": container})
        return payload

    def _create_stock_inventory_line_row(self, payload: payload) -> payload:
        """Fill the odoo 'stock.inventory' container with 'stock.inventory.line'
        records from purchase.table_done"""
        valid, failing = True, []
        oid = payload["container"].id
        products = [p for p in payload["inventory"].products if p.state.current() == "done"]
        for product in products:
            try:
                self.create("stock.inventory.line", product.as_inventory_payload(oid))
            except Exception:
                payload.update({"valid": False, "error_code": "odostockinvlinefail"})
                failing.append(product)
        payload.update({"failing": failing})
        return payload    

    def _propagate_start(self, payload: payload) -> payload:
        """use odoo action_start method to propagate inventory creation events"""
        payload["container"].action_start()
        payload["flag"] = False
        return payload

    def _propagate_validate(self, container: Record, autoval: bool) -> None:
        """use odoo action_validate methdod to automaticaly validate an inventory"""
        if autoval:
            try:
                container.action_validate()
            except Exception:
                # catch marshall error & pass it
                pass




