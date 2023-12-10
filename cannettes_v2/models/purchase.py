from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime
from collections import defaultdict
from erppeek import Record, RecordList
from typing import Any, Dict, List, Optional

from cannettes_v2.models.product import Product
from cannettes_v2.models.state_handler import PRODUCT_STATE, State, PROCESS_STATE, PURCHASE_STATE
from cannettes_v2.odoo.odoo import Odoo

Uuid = str
Payload = Dict[str, Any]


class Supplier(object):
    """parse Supplier record"""
    def __init__(self, *, partner: Optional[Record]= None) -> None:
        self.id = None
        self.name = None
        if partner:
            self.id = partner.id
            self.name = partner.name


class Purchase(object):
    """

    Attr:
        :oid: (int) Odoo purchase.order id.
        :name: (str) Odoo name for the Purchase
        :supplier: (Supplier) Supplier references.
        :create_date: (datetime) Odoo Purchase creation datetime
        :added_date: (datetime) Datetime of addition on the application.
        :_initial_products: (List[Products]) initial list products. remain immutable.
        :_state: (str) Current state of the purchase -> ['incoming', 'received']
        :_process_state: (str) Current processing state of the purchase -> ["None", "Started", "finished", "done"]

        :products: (List[Product])
        :uuid_registry: (Dict[uuid, Product])
        :pid_registry: (Dict[pid, Product])
        :barcode_registry: (Dict[barcode, Product])
    """

    def __init__(
        self,
        *,
        oid: int,
        name: str = "",
        supplier: Optional[Supplier] = None,
        create_date: datetime,
        state: State = State(PURCHASE_STATE),
        process_state: State = State(PROCESS_STATE),
        _initial_products: List[Product],
    ) -> None:
        self.oid = oid
        self.name = name
        self.supplier = supplier
        self.create_date = create_date
        self._initial_products = _initial_products
        self.state = state
        self.process_state = process_state
        self.added_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.build_registeries()

    def __repr__(self) -> str:
        return f"<{self.oid} {self.name} : {self.state} | {self.process_state}>"

    def build_registeries(self) -> None:
        self.uuid_registry: Dict[str, Product] = {}
        self.pid_registry: Dict[str, Product] = {}
        self.barcode_registry: Dict[int, Product] = {}
        self.products: List[Product] = []
        for ref in self._initial_products:
            product = deepcopy(ref)
            self.products.append(product)
            self.register_product(product)

    def register_product(self, product: Product) -> None:
        self.uuid_registry[product.uuid] = product
        self.register_barcodes(product)
        if product.pid:
            self.pid_registry[product.pid] = product

    def register_barcodes(self, product: Product) -> None:
        for brcd in product.barcodes:
            if brcd:
                self.barcode_registry[brcd] = product

    def get_modified_products(self) -> List[Uuid]:
        return [p.uuid for p in self.uuid_registry.values() if p._modified]

    def get_new_products(self) -> List[Uuid]:
        return [p.uuid for p in self.uuid_registry.values() if p._new]

    def get_unknown_products(self) -> List[Uuid]:
        return [p.uuid for p in self.uuid_registry.values() if p._unknown]

    def get_scanned_products(self) -> List[Uuid]:
        return [p.uuid for p in self.uuid_registry.values() if p._scanned]

    def retrieve_initial_product(self, product: Product) -> Product:
        return [p for p in self._initial_products if p.uuid == product.uuid][0]

    def update(self, payload: Payload) -> None:
        for k, v in payload.items():
            current = getattr(self, k, None)
            if current is None:
                raise KeyError(f"{self} : {k} attribute doesn't exist")
            if type(current) != type(v) and current is not None:
                raise TypeError(
                    f"{self} : field {k} value {v} ({type(v)}) does not match current type ({type(current)})"
                )
            setattr(self, k, v)

    def add_product(self, product: Product, with_initial: bool = False) -> None:
        self.products.append(product)
        self.register_product(product)
        if with_initial:
            self._initial_products.append(deepcopy(product))

    def del_product(self, product: Product, with_initial: bool = False) -> None:
        self.uuid_registry.pop(product.uuid, None)
        [self.barcode_registry.pop(brcd) for brcd in product.barcodes]
        self.pid_registry.pop(product.pid, None)
        self.products.pop(self.products.index(product))
        if with_initial:
            initial_product = self.retrieve_initial_product(product)
            index = self._initial_products.index(initial_product)
            self._initial_products.pop(index)

    def update_product(
        self, product: Product, payload: Payload, with_initial: bool = False
    ) -> None:
        if with_initial:
            initial_product = self.retrieve_initial_product(product)
            initial_product.update(payload)
            
        barcodes = payload.pop("barcodes", None)
        if barcodes and barcodes != product.barcodes:
            [self.barcode_registry.pop(brcd) for brcd in product.barcodes]
            product.update({"barcodes": barcodes})
            self.register_barcodes(product)
        product.update(payload)

    def build_initial_payload(self) -> Payload:
        payload = defaultdict(list)
        [payload[p.state.current()].append(p.to_payload()) for p in self.products]
        return payload

    def rebase_products(
        self, products: List[RecordList], api: Odoo
    ) -> Payload:
        """Pid are supposed to be unique accross the purchased product list."""
        for pur in products:
            product = self.pid_registry.get(pur.product_id.id, None)
            if product and pur.state == "cancel":
                self.del_product(product, with_initial=True)
            elif product and pur.state != "cancel":
                self.update_product(
                    product,
                    {
                        "name": re.sub(
                            "\[.*?\]",  # noqa: W605
                            "",
                            api.get_name_translation(pur.product_id),
                        ),
                        "barcode": api.get_barcodes(pur),
                        "qty": pur.product_qty,
                        "qty_package": pur.product_qty_package,
                    },
                    with_initial=True,
                )

            elif product is None:
                product = api.product_factory(product)
                self.add_product(product, with_initial=True)

    def update_edited_product(self, context: Payload) -> Payload:
        """Handle move and qty modification + move."""
        product = self.uuid_registry.get(context["uuid"], None)
        product.state.bump_to("done")
        product.update({"_scanned": True})
        if context["type"] == "mod":
            product.update({"qty_received": context["new_qty"], "_modified": True})
        context.update({"res": product.to_payload()})
        return context

    def search_scanned_in_self(self, context: Payload, **kwargs) -> Payload:
        product = self.barcode_registry.get(context["barcode"], None)
        print("self ", product)
        if product:
            product.update({"_scanned": True})
            product.state.bump()
            context.update({
                "flag": False,
                "res": {"product": product}
            })
        return context

    def search_scanned_in_odoo(
        self, context: Payload, api: Odoo, **kwargs
    ) -> Payload:
        product = api.search_product_from_barcode(context["barcode"])
        if product:
            payload = api.prepare_product_from_record(
                product, 
                _new=True, 
                _scanned=True,
                state = State(PRODUCT_STATE, 2)
            )
            context.update({
                "flag": False,
                "external": True,
                "res": {"product": Product(**payload)}
            })
        return context

    def build_external_product(self, context: Payload, **kwargs) -> Payload:
        product = Product(
            barcodes=[context["barcode"]],
            state=State(PRODUCT_STATE, 2),
            _new=True,
            _scanned=True,
            _unknown=True,
        )
        context.update({
            "flag": False,
            "external": True,
            "res": {"product": product}
        })
        return context

    def update_scanned_product(self, context: Payload, **kwargs) -> Payload:
        product = self.barcode_registry.get(context["barcode"], None)
        product.state.bump_to("queue")
        return context

    def is_starting(self):
        self.process_state.bump_to("starting")

    def is_finished(self):
        self.state.bump_to("received")
        self.process_state.bump_to("finished")

    def is_validated(self):
        self.state.bump_to("received")
        self.process_state.bump_to("done")

class Inventory(Purchase):
    def __init__(
        self,
        *,
        oid: int,
        catid: Optional[int] = None, 
        name: str = "",
        state: State = State(PURCHASE_STATE),
        process_state: State = State(PROCESS_STATE),
        _initial_products: List[Product],
    ) -> None:
        self.oid = oid
        self.catid = catid
        self.name = name
        self.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._initial_products = _initial_products
        self.state = state
        self.process_state = process_state
        self.added_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.build_registeries()

    def assembler(self, other: Inventory) -> None:
        """Product of both should be deepcopy do that uuid are the same."""
        for product in other.products:
            ref = self.uuid_registry.get(product.uuid, None)
            if ref:
                ref.qty_received += product.qty_received
            else:
                self.add_product(product)

    def nullifier(self) -> None:
        for product in self.products:
            if product.state != "done":
                product.update({"qty_received": 0, "_scanned": True})
                product.state.bump_to("done")


class PseudoPurchase(Purchase):
    pass

class PseudoInventory(Inventory):
    pass