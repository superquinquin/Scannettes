
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Any, Union

from cannettes_v2.odoo.odoo import Odoo
from cannettes_v2.models.purchase import Purchase, Supplier
from cannettes_v2.utils import format_error_cases

class Inventories(Odoo):

    def get_product_categories(self, cache: Dict[str, Any]) -> Dict[str, Any]:
        """fill cache with exist categories"""

        categories = self.browse(
            "product.category", [(["create_date", ">", "1900-01-01 01:01:01"])]
        )
        cat = sorted(
            [(c.complete_name, c.id) for c in categories],
            key=lambda x: x[0],
            reverse=False,
        )
        cache["odoo"]["inventory"]["type"] = cat
        return cache

    def generate_inv_product_table(self, cat_id: int) -> pd.DataFrame:
        """takes a category id as input, generate list of product records from this categ
            products records are : pp id, pt name, pp or pmb barcode, pt stock qty

        Args:
            cat_id (int): reference to a category

        Returns:
            List: list of all products records with input cat id.
        """

        def get_barcode() -> Union[str, bool]:
            barcode = pp.barcode
            if not barcode and pmb:
                for p in pmb:
                    if p.barcode:
                        barcode = p.barcode
                        break
            return barcode

        def get_name_translation() -> str:
            name = None
            for t in irt:
                if t.name == "product.template,name":
                    name = t.value
                    break
            if not name:
                name = pt.name
            return name

        # name, barcode or multiple barcode, theoric qty, real quantity
        product_list = []
        products = self.browse(
            "product.template", [("categ_id", "=", cat_id), ("active", "=", True)]
        )
        for pt in products:
            tmpl_id = pt.id
            irt = self.browse("ir.translation", [("res_id", "=", tmpl_id)])
            pp = self.get("product.product", [(["product_tmpl_id", "=", tmpl_id])])
            pmb = self.browse("product.multi.barcode", [(["product_id", "=", pp.id])])
            name = get_name_translation()
            qty = pt.qty_available
            virtual = pt.virtual_available
            id = pp.id
            barcode = get_barcode()
            product_list.append([barcode, id, name, qty, virtual, qty])

        columns = ["barcode", "id", "name", "qty", "virtual_qty", "qty_received"]
        table = pd.DataFrame(product_list, columns=columns)
        table.fillna(0, inplace=True)
        return table

    def create_inventory(self, input: Dict[str, Any], cache: Dict[str, Any], table: pd.DataFrame) -> int:
        """CREATE A PURCHASE OBJECT

        Args:
            input (dict): odoo cat_id
            data (dict): cache data dict
            table (pd.DataFrame): object origin table

        Returns:
            int: object_id that reference the object into
                cache['odoo']['inventory']['ongoing'][object_id]
        """

        def get_id() -> int:
            ongoing = list(cache["odoo"]["inventory"]["ongoing"].keys())
            processed = list(cache["odoo"]["inventory"]["processed"].keys())
            done = list(cache["odoo"]["inventory"]["done"].keys())
            m = max(ongoing + processed + done, default=0)
            return m + 1

        object_id = get_id()
        cat_id = input["object_id"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        inventory = Purchase(
            object_id,
            [x[0] for x in cache["odoo"]["inventory"]["type"] if x[1] == cat_id][
                0
            ],  # get name from the categ type list
            Supplier(None, "inventaire"),
            True,
            "inventory",
            now,
            now,
            "incoming",
            table,
        )

        cache["odoo"]["inventory"]["ongoing"][object_id] = inventory
        return object_id

    def post_inventory(self, inventory: Purchase, cache: Dict[str, Any], autoval: bool) -> bool:
        """MAIN AND ONLY INTERACTION PROCESS WITH ODOO FOR INVENTORIES OTHER THAN
          THAN FETCHING TEMPLATE DATA
          INVENTORIES ARE ONLY ADDED INTO ODOO AT VALIDATION PROCESS

        THUS
        !!! PRODUCTS ARE NOT BLOCKED IN ODOO AND CAN BE MANIPULATED, SALED...       !!!
        !!! IT IS STRONGLY RECOMMENDED DURING INVENTORIES TO STOP ANY OTHER PROCESS !!!
        !!! THAT COULD AFFECT INVENTORIED PRODUCTS                                  !!!

        STEPS
        @CHECKS if products do exist in odoo product.product table, break the process
                if product is found unmatched. A manual add is recquired to be abble to complete this check
        @CREATE A 'stock.inventory' row that will be used as a container for uour inventoried products
        @CREATE 'stock.inventory/line' for each purchase table_done products

        @PROPAGATE START, validate the inventory and its lines.
        @PROPAGATE VALIDATION, optionnal input from user, remove recquired manual validation

        Args:
            inventory (Purchase): purchase object containing related inventory data
            data (Dict): cache data dict

        Returns:
            bool: process state record
        """
        odoo_exist = self.check_item_odoo_existence(inventory.table_done)
        if odoo_exist["validity"] == False:
            # DATA VALIDITY IS TO BE PASSED TO ODOO
            return {
                "validity": False,
                "failed": "odoo_exist",
                "errors": odoo_exist["errors"],
            }

        print("test1 passed")
        p1 = self.create_stock_inventory_row(inventory)
        if p1["validity"] == False:
            # fail at creating a stock.inventory row
            return {"validity": False, "failed": "inv_row", "errors": p1["errors"]}

        p2 = self.create_stock_inventory_line_row(inventory, p1["container"])
        if p2["validity"] == False:
            # fail at creating one or more stock.inventory.line
            return {"validity": False, "failed": "inv_line_row", "errors": p2["errors"]}

        c = self.propagate_start(p2["container"])
        self.propagate_validate(c, autoval)
        return {"validity": True, "failed": "none", "errors": []}

    def create_stock_inventory_row(self, inventory: Purchase):
        """create a 'stock.inventory' container to be filled with inventory lines"""
        date = datetime.now().strftime("%d-%m-%Y")
        name = f"{inventory.name} {date}"
        validity = True
        try:
            container = self.create(
                "stock.inventory",
                {"name": name, "filter": "categories", "location_id": 12},
            )
        except Exception:
            # handle odoo errors on row creation
            container = None
            validity = False

        return {"validity": validity, "container": container, "errors": []}

    def create_stock_inventory_line_row(self, inventory: Purchase, container: object):
        """Fill the odoo 'stock.inventory' container with 'stock.inventory.line'
        records from purchase.table_done"""
        validity, errors = True, []
        _, _, records = inventory.get_table_records()
        for r in records:
            product = self.get("product.product", [("id", "=", r["id"])])
            uom = product.product_tmpl_id.uom_id.id
            try:
                self.create(
                    "stock.inventory.line",
                    {
                        "product_qty": r["qty_received"],
                        "product_id": r["id"],
                        "product_uom_id": uom,
                        "location_id": 12,
                        "inventory_id": container.id,
                    },
                )

            except Exception:
                # handle odoo erppeek erros
                validity = False
                errors.append(
                    format_error_cases(
                        "inv_block", {"barcode": product.barcode, "product": product}
                    )
                )

        return {"validity": validity, "container": container, "errors": errors}

    def propagate_start(self, container: object):
        """use odoo action_start method to propagate inventory creation events"""
        container.action_start()
        return container

    def propagate_validate(self, container: object, autoval: bool):
        """use odoo action_validate methdod to automaticaly validate an inventory"""
        if autoval:
            try:
                container.action_validate()
            except Exception:
                # catch marshall error & pass it
                pass

    def build(
        self,
        cache: Dict[str, Any],
        erp: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        self.connect(**erp)
        return self.get_product_categories(cache)


