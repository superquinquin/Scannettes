
# >>>>>>>>>>>>>>>>>>>>>>>>>> new version (unfinished)
import re
from erppeek import Record, RecordList
from typing import Optional, Any, List, Dict
from datetime import datetime, timedelta

from cannettes_v2.odoo.odoo import Odoo
from cannettes_v2.odoo.lobby import Lobby
from cannettes_v2.models.product import Product
from cannettes_v2.models.purchase import Purchase, Supplier
from cannettes_v2.models.state_handler import State, PURCHASE_STATE, PROCESS_STATE, PRODUCT_STATE

cache = Dict[str, Any]

class Deliveries(Odoo):
    def __init__(self) -> None:
        super().__init__()
        self.purchases: Dict[int, Optional[Purchase]] = {}
        self.last_update: datetime = None

    def fetch_purchases(self, cache: cache) -> None:
        delta = cache["config"]["time_delta"]
        lobby = cache.cache["lobby"]

        date_ceiling = self.get_update_time_ceiling(delta)
        purchases = self.browse(
            "purchase.order", 
            [
                ("create_date", ">", date_ceiling),
                ("id", "in", self.purchases.keys())
            ]
        ) 
        self.purchase_factory(purchases, lobby)
        self.last_update = datetime.now().date().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_update_time_ceiling(self, delta: List[int]) -> datetime:
        ceiling = self.last_update
        if ceiling is None:
            Y, M, W, D = delta
            now = datetime.now().date()
            ceiling = now + timedelta(years=-Y, months=-M, weeks=-W, days=-D)
            ceiling = ceiling.strftime("%Y-%m-%d %H:%M:%S")
        return ceiling
    
    def purchase_factory(self, purchases: RecordList, lobby: Lobby) -> None:
        
        for pur in purchases:
            oid = pur.oid
            name = pur.name
            _state = pur.state

            if _state == "draft":
                self.purchases[oid] = None

            elif _state == "purchase":
                _picking_state = self.get_picking_state(name)
                
                if _picking_state == "cancel":
                    self.purchases.pop(oid)
                    rid = lobby.find_room_associated_to_purchase(oid)
                    if rid:
                        lobby.delete_room(rid) # find room_id
                    
                elif _picking_state == "done":
                    purchase = self.purchases.get(oid)
                    purchase.state.bump_to("received")
                    purchase.process_state.bump_to("done")
                    rid = lobby.find_room_associated_to_purchase(oid)
                    if rid:
                        room = lobby.rooms.get(rid)
                        room.state.bump_to("done")
                elif _picking_state == "assigned" and self.purchases.get(oid, False):
                    purchase = self.purchases.get(oid)
                    products = self.fetch_products(purchase.name)
                    purchase.rebase_products(products, self)
                
                elif _picking_state == "assigned" and self.purchases.get(oid, False) is False:
                    purchase = {
                        "oid": oid,
                        "name": name,
                        "create_date": pur.create_date,
                        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "supplier": Supplier(pur.partner_id),
                        "_initial_products": self.fetch_products(name),
                        "state": State(PURCHASE_STATE),
                        "process_state": State(PROCESS_STATE),
                    }
                    self.purchases[oid] = Purchase(**purchase)

    
    def fetch_products(self, purchase_name: str) -> List[Product]:
        moves = self.browse("stock.move", [("origin", "=", purchase_name)])
        return [self.product_factory(product) for product in moves if product.state == "assigned"]

    def product_factory(self, product: Record):
        payload = {
            "pid": product.product_id.id,
            "name": re.sub("\[.*?\]", "", self.get_name_translation(product.product_id)),
            "barcode": self.get_barcodes(product),
            "qty": product.product_qty,
            "qty_virtual": None,
            "qty_package": product.product_qty_package,
            "state": State(PRODUCT_STATE)
        }
        return Product(**payload)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< 


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> (old version)
import re
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

from cannettes_v2.models.purchase import Purchase
from cannettes_v2.odoo.lobby import Lobby
from cannettes_v2.odoo.odoo import Odoo
from cannettes_v2.utils import get_ceiling_date, format_error_cases


class Deliveries(Odoo):


    def get_purchase(self, timeDelta: list, data: dict) -> dict:
        """
        Collect tracked Odoo Purchases adn group them in sub-groups based on pruchase & picking state ['draft', 'incoming', 'received', 'done'].
        Purchase state : ['draft', 'purchase', 'cancel'], draft = price requeste, purchase = purchase incoming.
        picking state : ['assigned', 'done', 'cancel'], assigned = stock move awaiting to be verified, done = stock move verified


        Tracking pruchases:
        Inside timeDelta, newly added purchases between 2 update
        Previously classified as Draft. Following state evolution, either move the purchase to later stage or keep it as draft.
        Currently incoming / received purchases. Track purchase content, by searching for any modificaton/ cancellation on the parchase. Update it if necessary.

        @timeDelta : list [YEAR, MONTH, WEEK, DAY] as time difference between Now and targeted date.
        > time range for tracking purchases. Supplented by last get_purchase activation date if any.
        @data: cache data dict

        Return Modification to nested dict data['odoo']['purchases'] and data['odoo']['history']['update_purchase']
        """
        draft = list(data["odoo"]["purchases"]["draft"].keys())
        incoming = list(data["odoo"]["purchases"]["incoming"].keys())
        received = list(data["odoo"]["purchases"]["received"].keys())
        done = list(data["odoo"]["purchases"]["done"].keys())
        date_ceiling = get_ceiling_date(timeDelta, data, "update_purchase")
        purchasesList = (
            self.browse("purchase.order", [("create_date", ">", date_ceiling)])
            + self.browse("purchase.order", [("id", "in", draft)])
            + self.browse("purchase.order", [("id", "in", incoming)])
            + self.browse("purchase.order", [("id", "in", received)])
        )
        data["odoo"]["purchases"]["draft"] = {}  # reset to avoid duplicate

        for pur in purchasesList:
            # pur.states ['draft','purchase','cancel']
            id, name, purchase_state, create_date = (
                pur.id,
                pur.name,
                pur.state,
                pur.create_date,
            )

            if purchase_state == "purchase" and id not in done:
                print(name, "-", create_date)
                picking_state = self.get_picking_state(
                    name
                )  # ['assigned, cancel, done']

                if picking_state == "cancel":
                    # then remove the purchase
                    Lobby().remove_room_associated_to_purchase(data, id)
                    self.remove_purchase(data, id)
                elif picking_state == "done":
                    # then pass it to done dict adn remove it from previous dict
                    exist = Lobby().update_room_associated_to_purchase(data, id, "done")
                    if exist:
                        # room associated  exist, update purchase
                        self.move_purchase(data, id, "done")
                        data["odoo"]["purchases"]["done"][id].change_status(
                            "received", "verified"
                        )
                    else:
                        # room not exist, then no need to keep purchase
                        self.remove_purchase(data, id)

                elif picking_state == "assigned":
                    if id not in incoming + received:
                        self.add_purchase(pur, name, id, data)
                    else:
                        # in case modification has been made
                        if id in incoming:
                            purchase = data["odoo"]["purchases"]["incoming"][id]
                            self.recharge_purchase(purchase, data)
                        elif id in received:
                            purchase = data["odoo"]["purchases"]["received"][id]
                            self.recharge_purchase(purchase, data)

            elif purchase_state == "draft":
                data["odoo"]["purchases"]["draft"][
                    id
                ] = None  # Placeholder to keep tracking drafts

        data["odoo"]["history"]["update_purchase"].append(
            datetime.now().date().strftime("%Y-%m-%d %H:%M:%S")
        )
        return data

    def add_purchase(self, pur, name: str, id: str, data: dict):
        """add purchase into the cache"""
        items = []
        supplier = pur.partner_id
        create_date = pur.create_date
        added_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        moves = self.browse("stock.move", [("origin", "=", name)])
        for item in moves:
            if item.state == "assigned":
                items.append(
                    [
                        self.get_barcode(item),  # item.product_id.barcode
                        item.product_id.id,
                        re.sub(
                            "\[.*?\]", "", self.get_name_translation(item.product_id)
                        ).strip(),
                        item.product_qty,
                        item.product_qty_package,
                        0,
                    ]
                )

        table = pd.DataFrame(
            items, columns=["barcode", "id", "name", "qty", "pckg_qty", "qty_received"]
        )
        data["odoo"]["purchases"]["incoming"][id] = Purchase(
            id,
            name,
            supplier,
            True,
            "purchase",
            create_date,
            added_date,
            "incoming",
            table,
        )

    def remove_purchase(self, data: Dict, id: int):
        """handle remove a purchase during get_purchase method"""

        if id in list(data["odoo"]["purchases"]["incoming"].keys()):
            data["odoo"]["purchases"]["incoming"].pop(id)

        elif id in list(data["odoo"]["purchases"]["received"].keys()):
            data["odoo"]["purchases"]["received"].pop(id)

        elif id in list(data["odoo"]["purchases"]["done"].keys()):
            data["odoo"]["purchases"]["done"].pop(id)

    def move_purchase(self, data: Dict, id: int, dest: str):
        """handle move purchase during get_purchase method"""
        if (
            id in list(data["odoo"]["purchases"]["incoming"].keys())
            and dest != "incoming"
        ):
            data["odoo"]["purchases"][dest][id] = data["odoo"]["purchases"]["incoming"][
                id
            ]
            data["odoo"]["purchases"]["incoming"].pop(id)

        elif (
            id in list(data["odoo"]["purchases"]["received"].keys())
            and dest != "received"
        ):
            data["odoo"]["purchases"][dest][id] = data["odoo"]["purchases"]["received"][
                id
            ]
            data["odoo"]["purchases"]["received"].pop(id)

        elif id in list(data["odoo"]["purchases"]["done"].keys()) and dest != "done":
            data["odoo"]["purchases"][dest][id] = data["odoo"]["purchases"]["done"][id]
            data["odoo"]["purchases"]["done"].pop(id)

    def check_item_alt_integrity(self, item) -> Dict:
        """request odoo for main and mulitbarcode products
        WHEN ALTS, CHECKS ALT ID AND BARCODE CONSISTENCIES

        RETURN ITEM VALIDITY CHECK
        """
        item_barcode, item_id = item[0], item[1]
        main = self.get("product.product", [("id", "=", item_id)])
        alts = self.browse("product.multi.barcode", [("barcode", "=", item_barcode)])

        def check_alt():
            # verify if all ids are same
            # verify if all barcodes are the same
            try:
                if not main:
                    check_i, check_b = alts[0].product_id.id, alts[0].product_id.barcode
                else:
                    check_i, check_b = main.id, main.barcode
            except IndexError:
                return False

            for alt in alts:
                barcode = alt.product_id.barcode
                id = alt.product_id.id
                if check_i != id or check_b != barcode:
                    return False
            return True

        if not item_barcode or not main:
            ## no product has barcode
            return {
                "item_validity": False,
                "alt": None,
                "has_main": False,
                "product": None,
            }

        elif not main.barcode and alts:
            # main product has no barcode, barcode is on alt
            # but multiple alts
            return {
                "item_validity": check_alt(),
                "alt": alts[0],
                "has_main": False,
                "product": None,
            }

        elif main.barcode and alts:
            print("both questionnable")
            return {
                "item_validity": check_alt(),
                "alt": alts[0],
                "has_main": True,
                "product": main,
            }

        else:
            # only main
            print("only main")
            return {
                "item_validity": True,
                "alt": None,
                "has_main": True,
                "product": main,
            }

    def check_item_odoo_existence(self, table: pd.DataFrame) -> dict:
        """CHECKS IF ITEMS TO BE SENT TO ODOO ARE
          INDEED EXISTING IN ODOO PRODUCT.PRODUCT TABLE

        CHECKS CROSS VALIDATION OF PRODUCTS IDs AND BARCODE

        TEST CAN RAISE MANY PROBLEMS DUE TO ODOO DATABASE UNCONSISTENCIES
        @multi_items
        @...

        Args:
            table (pd.DataFrame): purchase object Table_done to check

        Returns:
            dict: test valididy
        """
        errors = []  # dict(barode, product, hint placeholder)
        validity = True

        for item in table.values.tolist():
            item_barcode = item[0]
            item_id = item[1]
            result = self.check_item_alt_integrity(item)
            result["barcode"] = item_barcode
            item_validity = result["item_validity"]
            print("__", item_barcode, "-", item_id)
            print("valid__", item_validity)

            if item_validity:
                odoo_alt = result["alt"]
                if not result["has_main"]:
                    odoo_barcode = odoo_alt.barcode
                    odoo_id = odoo_alt.product_id.id
                else:
                    odoo_barcode = self.get(
                        "product.product", [("id", "=", item_id)]
                    ).barcode
                    odoo_id = self.get(
                        "product.product", [("barcode", "=", item_barcode)]
                    ).id
                    odoo_alts = self.browse(
                        "product.multi.barcode", [("product_id", "=", item_id)]
                    ).barcode

                if item_id != odoo_id or (
                    item_barcode != odoo_barcode and item_barcode not in odoo_alts
                ):
                    print("_", odoo_barcode, "has a problem")
                    ## ITEM VALIDITY FALSE
                    ### CASE BARCODE IS FALSE :: NO BARCODE PRODUCT
                    ### CASE ID AND BARCODE DO NOT MATCH
                    item_validity = False
                    validity = False
                    # test arror handling
                    errors.append(format_error_cases("unmatch", result))
                    continue

            else:
                ## ITEM VALIDITY IS FALSE
                ###CASE ALT == NONE && HAS_MAIN == FALSE: PREDUCT NOT IN ODOO
                ###CASE ALT == NOT NONE && HAS_MAIN == TRUE: PREDUCT HAS DUPLICATES IN MULTI && PROD.PROD
                ###CASE ALT == NOT NONE && HAS_MAIN == FALSE: PREDUCT HAS DUPLICATES INSIDE MULTI BARCODE SUPPOSED NOT HAPPEN HANDLE IT ANYWAY
                # Odoo database problem where a product barcode refer to multiple products...
                print("__", item_barcode, "__")
                item_validity = False
                validity = False
                # test error handling
                errors.append(format_error_cases("item_validity", result))
                continue

        return {"validity": validity, "errors": errors}

    def check_item_purchase_existence(
        self, purchase, table: pd.DataFrame, create: bool
    ) -> dict:
        """CHECK IF ITEMS ARE INDEED IN ODOO PURCHASE

        WHEN product not found and config apply auto item creation,
        the item will be automatically created,
        otherwise break validation process and request manual item add

        Args:
            purchase (_type_): Purchase object to check
            table (pd.DataFrame): purchase table_done to check
            create (bool): create item or not when unmatched

        Returns:
            dict: test results and valididy
        """
        errors = []
        validity = True
        id = purchase.id
        name = purchase.name

        for item in table[["barcode", "id"]].values.tolist():
            item_validity = True
            item_barcode = item[0]
            item_id = item[1]
            item_state = self.get_item_state(name, item_id)

            if item_state == "none" and create:
                # Create purchase item in odoo
                print("init item creation")
                passed = self.create_purchase_record(purchase, item_id)
                if passed == False:
                    validity = False
                    ## errors handling
                    errors.append(
                        format_error_cases(
                            "creation_no_exist",
                            {
                                "barcode": item_barcode,
                                "product": self.get(
                                    "product.product", [("id", "=", item_id)]
                                ),
                            },
                        )
                    )

            elif item_state == "none" and create == False:
                validity = False
                ## errors handling
                errors.append(
                    format_error_cases(
                        "creation_inactivated",
                        {
                            "barcode": item_barcode,
                            "product": self.get(
                                "product.product", [("id", "=", item_id)]
                            ),
                        },
                    )
                )

        return {"validity": validity, "errors": errors}

    def post_products(self, purchase: Purchase):
        """apply received qty in odoo for eachs received items of the purchase"""
        name = purchase.name
        moves = self.browse("stock.move", [("origin", "=", name)])
        for move in moves:
            print("--", move.product_id)
            move_id = move.id
            move_state = move.state
            item_id = move.product_id.id

            if move_state == "assigned" and purchase.is_received(item_id):
                received_qty = purchase.get_item_received_qty(item_id)
                self.apply_purchase_record_change(move_id, received_qty)

    def post_purchase(self, purchase: Purchase, data: dict, autoval: bool) -> dict:
        """METHOD TO SEND PURCHASE DATA BACK INTO ODOO, APPLYING RECEIVED QTY MODFICATION
          AND AUTO VALIDATION WHEN TRUE
          to avoid any clash, crash and errors back into odoo database, the post processus
          follow restrictive checks that stops the process at any abnormality found.

          The post process takes only care about purchase.table_done products,
          table_queue and table_entries are neglected and considered non-relevant.

          CHECKS
          @test1: checks if the purchase has not already been manually validated in odoo.
          @test2: checks if all table_done items are existing in odoo product.product table
                  in case, where a product do not exist, it is required to manually
                  add the product into odoo
          @test3: checks if all items from table_done are existing inside the its original odoo image,
                  IF ODOO_CREATE_NEW_PURCHASE_LINE config is True:
                    when an unmatched item is found, automatically add it into odoo purchase
                  IF ODOO_CREATE_NEW_PURCHASE_LINE config is False:
                    when an unmatched item is found, break processus. The item needs
                    to be manually added or removed from the application table

          If all test are passed, the data can be safely imported into odoo.
          it take all rpoducts from odoo purchase and apply its new received qty

          If autoval is True:
            Propagate the validation event. No manual validation in odoo is recquired.
          If autoval is False:
            Manual validation in odoo is recquired

        Args:
            purchase (Purchase): Purchase to be validated
            data (dict): cache data dict
            autoval (bool): wether propagate with an odoo auto validation
                            or keep manual odoo validation

        Returns:
            dict: validation state dict
        """
        purchase.process_status = "verified"
        name = purchase.name
        table = purchase.table_done

        # ====> verify that the purchase is not already validated
        picking_state = self.get_picking_state(name)
        if picking_state == "done":
            # already odoo validated, msg this information and block data transfer
            return {"validity": False, "failed": "validation_exist", "errors": [""]}

        # ====> purchase_item exist in ODOO
        odoo_exist = self.check_item_odoo_existence(table)
        if odoo_exist["validity"] == False:
            # DATA VALIDITY IS TO BE PASSED TO ODOO
            return {
                "validity": False,
                "failed": "odoo_exist",
                "errors": odoo_exist["errors"],
            }
        print("test1 passed")

        # <==== room item all in odoo purchase
        purchase_exist = self.check_item_purchase_existence(
            purchase, table, data["config"].ODOO_CREATE_NEW_PURCHASE_LINE
        )
        if purchase_exist["validity"] == False:
            # All product from the app are not in the odoo purchase object.
            # purchase items can be create if odoo_create_new_purchase_item == True
            return {
                "validity": False,
                "failed": "purchase_exist",
                "errors": purchase_exist["errors"],
            }
        print("test2 passed")

        # APPLY MODIFICATION TO ODOO ITEMS
        self.post_products(purchase)
        return {"validity": True, "failed": "none", "errors": []}

    def product_supplier_data(self, purchase, product):
        """retrieve supplier data for requested item
        Price and name
        Informations are nacessary in order to create new item row in odoo purchase
        return product name and price"""
        partner_item = self.get(
            "product.supplierinfo",
            [
                ("id", "=", purchase.supplier.id),
                ("product_tmpl_id.id", "=", product.product_tmpl_id.id),
            ],
        )

        if partner_item:
            price = partner_item.base_price
            product_code = partner_item.product_code

            if product_code:
                name = f"[{product_code}] {product.name}"

            else:
                name = product.name

        else:
            price = 1
            name = product.name

        return name, price

    def create_purchase_record(self, purchase: Purchase, item_id: int) -> bool:
        """USED IF ODOO_CREATE_NEW_PURCHASE_LINE=TRUE
        create item row into an odoo purchase.

        If the item is not found in product.product,
        the process fail and break post_purchase test3
        However this case should not happen as test2 has been sucessfull

        Args:
            purchase (Purchase): purchase object
            item_id (int): odoo product.prudct id

        Returns:
            bool: successfully created item
        """
        purchase_id = purchase.id
        product = self.get("product.product", [("id", "=", item_id)])
        if not product:
            return False

        uom = product.product_tmpl_id.uom_id.id
        name, price = self.product_supplier_data(purchase, product)
        new_item = {
            "order_id": purchase_id,
            "product_uom": uom,
            "price_unit": price,
            "product_qty": 1,  # 0
            "name": name,
            "product_id": product,
            "date_planned": datetime.now(),
        }

        self.create("purchase.order.line", new_item)
        return True

    def recharge_purchase(self, purchase: object, data: dict) -> None:
        """Request to update purchase data from odoo
        keep room table structure untouched
        In use when odoo is modified eg:
        new product added in odoo,
        change in quantity, pkg qty, name, barcode
        product supr
        ...
        return purchase object
        """

        id, name = purchase.id, purchase.name
        purchase_state = self.get("purchase.order", [("id", "=", id)]).state
        picking_state = self.get_picking_state(name)

        if purchase_state == "purchase" and picking_state == "assigned":
            ### LOOK FOR UPDATE
            moves = self.browse("stock.move", [("origin", "=", name)])

            for item in moves:
                product = {
                    "id": item.product_id.id,
                    "barcode": self.get_barcode(item),
                    "name": re.sub("\[.*?\]", "", item.name).strip(),
                    "qty": item.product_qty,
                    "qty_packaqe": item.product_qty_package,
                    "qty_received": 0,
                }
                purchase.recharge_item(product, purchase.process_status, item.state)

        elif purchase_state == "cancel" or picking_state == "cancel":
            # CANCELED: REMOVE PURCHASE
            if id in list(data["odoo"]["purchases"]["incoming"].keys()):
                data["odoo"]["purchases"]["incoming"].pop(id)

            elif id in list(data["odoo"]["purchases"]["received"].keys()):
                data["odoo"]["purchases"]["received"].pop(id)

    def delete_purchase(self, id: str, data: dict, object_type: str, state: str):
        """removed purchase from paired list"""
        if state == "done":
            if object_type == "purchase":
                data["odoo"]["purchases"]["done"].pop(id)
            else:
                data["odoo"]["inventory"]["done"].pop(id)

        elif state == "received":
            if object_type == "purchase":
                data["odoo"]["purchases"]["received"].pop(id)
            else:
                data["odoo"]["inventory"]["processed"].pop(id)
                
                
    def build(
        self,
        cache: Dict[str, Any],
        erp: Dict[str, Any],
        delta_search_purchase: List[int],
        **kwargs
    ) -> Dict[str, Any]:
        self.connect(**erp)
        return self.get_purchase(delta_search_purchase, cache)


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<