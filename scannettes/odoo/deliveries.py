from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional

from erppeek import Record, RecordList

from scannettes.models.product import Product
from scannettes.models.purchase import Purchase, Supplier

from scannettes.odoo.lobby import Lobby
from scannettes.odoo.odoo import Odoo
from scannettes.utils import get_update_time_ceiling

payload = Dict[str, Any]


class Deliveries(Odoo):
    def __init__(
        self, 
        *, 
        purchases: Dict[str, Purchase]= {}, 
        last_update: Optional[datetime]= None
        ) -> None:
        super().__init__()
        self.purchases: Dict[int, Optional[Purchase]] = purchases
        self.last_update: datetime = last_update
        
        self.export_pipeline = [
            self._check_product_odoo_existence,
            self._check_product_into_odoo_delivery,
            self._add_products_into_odoo_delivery,
            self._export_products
        ]


    @classmethod
    def initialize(cls, odoo_configs: payload, lobby:Lobby, init: payload= {}, **kwargs) -> Deliveries:
        delta = odoo_configs.get("delta_search_purchase", False)
        erp = odoo_configs.get("erp", False)
        if delta is False:
            raise KeyError("please configure odoo.delta_search_purchase")
        if erp is False:
            raise KeyError("You must configure odoo.erp payload")
        deliveries = cls(**init)
        deliveries.connect(**erp)
        deliveries.fetch_purchases(delta, lobby)
        return deliveries

    def as_backup(self) -> payload:
        return {"purchases": self.purchases, "last_update": self.last_update}

    def fetch_purchases(self, delta: List[int], lobby: Lobby) -> None:
        """
        collect purchases from "purchase.order"
        :states:
            :purchase_state: ('draft' > 'purchase', 'cancel')
            :draft: price is requested
            :purchase: prices and products has been accepted. the purchase order is on its way.
            :cancel: the purchase order has been canceled by one of both agents, during one of the previous phases.

        collect picking states from "stock.picking"
        :states:
            :picking_state: ('assigned' > 'done', 'cancel')
            :assigned: stock move awaiting to be verified. assigned happen when an order is in purchase state
            :done: stock move received and verified.
            :cancel: when purchase order has been canceled by one of both agent. should occur during purchase state.
            
        args:
            :cache: cached configs
        
        Collect purchased from last update datetime, if No previous update use config time_delta as floor for the search.
        keep track of purchased in "draft" state by referencing them as self.purchases keys ( value set to None )
        """        
        
        date_ceiling = get_update_time_ceiling(self.last_update, delta)
        cached_drafts = self.browse("purchase.order", [("id", "in", list(self.purchases.keys()))])
        new_purchases = self.browse("purchase.order", [("create_date", ">", date_ceiling)])
        purchases = cached_drafts + new_purchases
        
        self.purchase_factory(purchases, lobby)
        self.last_update = datetime.now().date().strftime("%Y-%m-%d %H:%M:%S")



    def purchase_factory(self, purchases: RecordList, lobby: Lobby) -> None:
        for pur in purchases:
            oid = pur.id
            name = pur.name
            _state = pur.state
            print(f"<{oid} - {name} : {_state}>")

            if _state == "draft":
                self.purchases[oid] = None

            elif _state == "purchase":
                _picking_state = self.get_picking_state(name)

                if _picking_state == "cancel": # -- UNTESTED
                    purchase = self.purchases.pop(oid, None)
                    rid = purchase.associated_rid
                    if rid:
                        lobby.delete_room(rid) 

                elif _picking_state == "done" and self.purchases.get(oid): # -- must contain the purchase
                    purchase = self.purchases.get(oid)
                    rid = purchase.associated_rid
                    if rid:
                        lobby.rooms.get(rid).is_validated()
                    if rid is None and purchase:
                        purchase.is_validated()
                        self.purchases.pop(oid)
                        
                elif _picking_state == "assigned" and self.purchases.get(oid, False): # -- UNTESTED
                    self.recharge_purchase(oid)

                elif (
                    _picking_state == "assigned"
                    and self.purchases.get(oid, False) is False
                ):
                    self.purchases[oid] = Purchase(
                        oid= oid,
                        name= name,
                        create_date= pur.create_date,
                        supplier= Supplier(partner=pur.partner_id),
                        _initial_products = self.fetch_products(name)
                    )

    def fetch_purchase_products(self, purchase_name: str, only_assigned:bool=True) -> List[RecordList]:
        cond = [("origin", "=", purchase_name)]
        if only_assigned:
            cond.append(("state", "=", "assigned"))
        return self.browse("stock.move", cond)
    
    def fetch_products(self, purchase_name: str) -> List[Product]:
        moves = self.fetch_purchase_products(purchase_name)
        return [self.product_factory(product) for product in moves]

    def product_factory(self, product: Record, **kwargs):
        name = self.get_name_translation(product.product_id.product_tmpl_id)
        prod = Product(**{
            "pid": product.product_id.id,
            "name": re.sub("\[.*?\]", "", name).strip(),
            "barcodes": self.get_barcodes(product.product_id),
            "qty": product.product_qty,
            "qty_package": product.product_qty_package,
            "uomid": product.product_id.product_tmpl_id.uom_id.id
        })
        prod.update(kwargs)
        return prod
    
    def get_associable_purchases(self) -> List[Purchase]:
        def _associable(pur: Optional[Purchase]) -> bool:
            return pur and pur.associated_rid is None and pur.process_state.current() != "done"
        return [pur for pur in self.purchases.values() if _associable(pur)]
    
    def export_to_odoo(self, oid: int, create_missing_product: bool= False, autoval: bool= False) -> payload:
        payload = {"container":None, "purchase": self.purchases.get(oid), "valid": True, "flag": True, "add_missing": create_missing_product}
        handlers = iter(self.export_pipeline) 
        while payload["flag"]:
            handler = next(handlers)
            payload = handler(payload)
            print(handler, payload)
            if payload["valid"] is False:
                return payload
        self._propagate_validate(payload["container"], autoval)
        return payload


    def _check_product_odoo_existence(self, payload: payload) -> payload:
        outsiders = payload["purchase"].get_unknown_products()
        payload.update({"valid": not any(outsiders), "failing": outsiders, "error_name": "odoout"})
        return payload
    
    def _check_product_into_odoo_delivery(self, payload: payload) -> payload:
        odoo_base = self.browse("stock.move", [("origin", "=", payload["purchase"].name)])
        odoo_pids = set([p.product_id.id for p in odoo_base])
        current_pids = set([p.pid for p in payload["purchase"].products])
        outsiders = list(current_pids - odoo_pids)
        payload.update({"valid": True, "failing": outsiders, "error_name": "purout"})
        return payload

    def _add_products_into_odoo_delivery(self, payload: payload) -> payload:
        if payload["add_missing"] is False and payload["failing"]:
            payload.update({"valid": False, "error_name": "purout"})
            return payload
        
        if payload["add_missing"] is False or not payload["failing"]:
            return payload
        
        purchase = payload["purchase"]
        for pid in payload['failing']:
            product = purchase.pid_registry.get(pid, None)
            self._inject_unknown_products(purchase, product)
        return payload
    
    def _inject_unknown_products(self, purchase: Purchase,  product: Product) -> payload:
        oprod = self.get("product.product", [("id", "=", product.pid)])
        if not product:
            return False

        name, price = self._product_supplier_data(purchase, oprod)
        self.create("purchase.order.line", product.as_purchase_payload(purchase.oid, price, name))
        return True

    def _product_supplier_data(self, purchase: Purchase, pp: Record) -> Tuple[str, int]:
        partners = self.browse(
            "product.supplierinfo",
            [
                ("id", "=", purchase.supplier.id),
                ("product_tmpl_id.id", "=", pp.product_tmpl_id.id),
            ],
        )

        price, name = 1, pp.name
        if partners:
            partner = partners[0]
            price = partner.base_price
            product_code = partner.product_code
            name = pp.name
            if product_code:
                name = f"[{product_code}] {pp.name}"
        return (name, price)

    def _export_products(self, payload: payload) -> None:
        moves = self.browse("stock.move", [("origin", "=", payload["purchase"].name), ("state", "=", "assigned")])
        for move in moves:
            mvid, pid = move.id, move.product_id.id
            product = payload["purchase"].pid_registry.get(pid, None)
            if product and product.state.current() == "done":
                self.apply_purchase_record_change(mvid, product.qty_received)
        payload["flag"] = False
        payload["container"] = moves
        return payload   
        


    def recharge_purchase(self, oid: str) -> None:
        purchase = self.purchases.get(oid)
        products = self.fetch_purchase_products(purchase.name, False)
        purchase.rebase_products(products, self)

    def _delete_purchase(self, oid: int) -> None:
        self.purchases.pop(oid)

    def _propagate_validate(self, container: Record, autoval: bool) -> None:
        """use odoo action_validate methdod to automaticaly validate an inventory"""
        if autoval:
            try:
                container.action_validate()
            except Exception:
                # catch marshall error & pass it
                pass