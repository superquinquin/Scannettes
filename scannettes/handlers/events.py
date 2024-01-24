from typing import Any, Dict, List, Tuple

from flask import current_app, url_for
from flask_socketio import emit, join_room

from scannettes import scannettes
from scannettes.authenticator import Authenticator
from scannettes.decorators import protected
from scannettes.odoo.lobby import Lobby
from scannettes.odoo.odoo import Odoo
from scannettes.odoo.deliveries import Deliveries
from scannettes.odoo.inventories import Inventories
from scannettes.models.purchase import Purchase, Inventory
from scannettes.tools.pdf import PDF
from scannettes.tools.backup import Cache
from scannettes.utils import build_validation_error_payload


Cache = Dict[str, Any]
Payload = Dict[str, Any]



@scannettes.socketio.on("message")
def log_message(msg):
    print(str(msg))
    
@scannettes.socketio.on("initialization-call")
def initialize(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    
    if context["instance"] == "lobby":
        context = {
            "origin": cache.config["flask"]["address"],
            "rooms": [room.to_payload() for room in lobby.get_open_rooms()]
        }
        join_room("lobby")
        emit("lobby-initialization", context , include_self=True)
        
    elif context["instance"] == "room":
        rid = context["rid"]
        room = lobby.rooms.get(int(rid))
        context = {
            "room": room.to_payload(),
            "data": [product.to_payload(single_brcd=True) for product in room.data.products]
        }
        join_room(str(rid))
        emit("room-initialization", context , include_self=True)
    


@scannettes.socketio.on("admin-initialization-call")
@protected(auth_level="admin")
def admin_initialize(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    deliveries: Deliveries = cache.deliveries

    if context["instance"] == "lobby":
        context = {
            "origin": cache.config["flask"]["address"],
            "rooms": [room.to_payload() for room in lobby.get_all_rooms()],
            "purchases": [pur.to_sel_tuple() for pur in deliveries.get_associable_purchases()],
            "categories": cache.inventories.categories,
        }
        join_room("lobby")
        emit("lobby-initialization", context , include_self=True)
    elif context["instance"] == "room":
        rid = context["rid"]
        room = lobby.rooms.get(rid)
        context = {
            "room": room.to_payload(),
            "data": [product.to_payload(single_brcd=True) for product in room.data.products]
        }
        join_room(str(rid))
        emit("room-initialization", context , include_self=True)
    

@scannettes.socketio.on("add-rooms")
@protected(auth_level="admin")
def add_room(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    inventories: Inventories = cache.inventories
    deliveries: Deliveries = cache.deliveries
    erp = cache.config["odoo"]["erp"]
    address = cache.config["flask"]["address"]
    
    adding_type = context.get("type", None)
    payload = {"state": "ok", "data": {"origin": address}}
    sel_payload = {"state": "ok", "data": {}}

    if adding_type == "purchase":
        oid = context.get("oid")
        purchase = deliveries.purchases.get(oid, None)
        context.update({"data": purchase})
        room = lobby.room_factory(context)
        rooms = [room.to_payload()]
        payload["data"]["rooms"] = rooms
        sel_payload["data"]["purchases"] = [pur.to_sel_tuple() for pur in deliveries.get_associable_purchases()]
        emit("add-rooms", payload ,include_self=True, broadcast=True)
        emit("update-purchase-selector", sel_payload, include_self=True, broadcast=True)
        
    elif adding_type == "inventory":
        context.update({"catid": context.get("oid")})
        inventories.connect(**erp)
        invs = inventories.inventory_siblings_factory(**context)
        (shelf, stock) = lobby.room_sibling_factory(context, *invs)
        rooms = [shelf.to_payload(), stock.to_payload()] 
        payload["data"]["rooms"] = rooms
        emit("add-rooms", payload ,include_self=True, broadcast=True)
                
    else:
        payload = {"state": "err", "data": {"message": "Création de salon: quelque chose n'a pas marché."}}
        emit("message", payload, include_self=True)
    emit("close-creation-modal", include_self=True)


@scannettes.socketio.on("del-rooms")
@protected(auth_level="admin")
def del_rooms(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    deliveries: Deliveries = cache.deliveries
    for rid in context["rids"]:
        lobby.delete_room(rid)
    sel_payload = {"state": "ok", "data": {"purchases": [pur.to_sel_tuple() for pur in deliveries.get_associable_purchases()]}}
    emit("del-rooms", {"state": "ok", "data": context}, include_self=True, broadcast=True)
    emit("update-purchase-selector", sel_payload, include_self=True, broadcast=True)
    
@scannettes.socketio.on("reinit-room")
@protected(auth_level="admin")
def reinit_rooms(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    lobby.reset_room(int(context["rid"]))
    emit("reinit-room", {"state": "ok", "data": context})
    


@scannettes.socketio.on("generate-qrcodes")
def generate_qrcodes(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    payload = lobby.qrcode_iterator(context)
    
    pdf = PDF("P", "mm", "A4")
    output = pdf.generate_pdf(payload)
    emit("qrcodes-pdf", {"pdf": output})



# -- ROOMS RELATED EVENTS

@scannettes.socketio.on("laser-scan")
def laser_scan(context):
    cache: Cache = current_app.cache
    config: Dict[str, Any] = cache.config
    lobby: Lobby = cache.lobby
    
    api = Odoo()
    api.connect(**config["odoo"]["erp"])
    room = lobby.rooms.get(int(context["rid"]))
    context = room.search_product("laser", context, api)
    
    if context["res"].get("scanned", False):
        res = context["res"]
        emit("laser-scan-scanned", res, include_self=True)
    else:
        res = {
            "rid": context["rid"], 
            "product": context["res"]["product"].to_payload(True)
        }
        emit("laser-scan", res, include_self=True)
        
    


@scannettes.socketio.on("modify-product")
def bump_product(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    room = lobby.rooms.get(int(context["rid"]))
    product = room.data.uuid_registry.get(context["uuid"])
    
    if context["modifications"]:
        context["modifications"]["qty_received"] = float(context["modifications"]["qty_received"]) # tmp
    else:
        product.status_quo()
        
    product.modify(
        context["has_modifications"],
        context["modifications"]
    )
    
    context["product"] = product.to_payload(True)
    emit("modify-product", context, include_self=True, broadcast=True, to=str(context["rid"]))
    

@scannettes.socketio.on("delete-products")
@protected(auth_level="admin")
def delete_products(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    room = lobby.rooms.get(int(context["rid"]))
    data = room.data
    for uuid in context["uuids"]:
        product = data.uuid_registry.get(uuid)
        data.del_product(product)
    emit("delete-products", context, include_self=True, broadcast=True, to=str(context["rid"]))


@scannettes.socketio.on("closing")
def closing(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    
    rid = int(context["rid"])
    room = lobby.rooms.get(rid)
    room.is_finished()
    
    context = {"state": "ok", "data": {"rid": str(rid), "assembling": False}}
    if room.type == "inventory" and room.sibling is not None and lobby.can_assemble(rid, room.sibling):
        sibling = room.sibling
        new_room = lobby.assembling_rooms(rid, sibling)
        context["data"] = {
            "room": new_room.to_payload(),
            "assembling": True,
            "rid": str(rid),
            "sibling": sibling
        }
    emit("closing", context,  broadcast=True, to="lobby")
    emit("closing", {"origin": cache.config["flask"]["address"]}, include_self=True, broadcast=True, to=str(rid))
    
    
    

@scannettes.socketio.on("validation")
@protected(auth_level="admin")
def validation(context):
    cache: Cache = current_app.cache
    config: Dict[str, Any] = cache.config
    lobby: Lobby = cache.lobby
    room = lobby.rooms.get(int(context["rid"]))
    
    accept_new_lines = config["odoo"].get("odoo_create_new_purchase_line", True)
    auto_val = config["odoo"].get("odoo_auto_purchase_validation", False)
    
    oid = room.data.oid

    if room.type == "purchase":
        deliveries: Deliveries = cache.deliveries
        deliveries.connect(**config["odoo"]["erp"])
        payload = deliveries.export_to_odoo(
            oid,
            accept_new_lines,
            auto_val,      
        )
    else:
        inventories: Inventories = cache.inventories
        inventories.connect(**config["odoo"]["erp"])
        payload = inventories.export_to_odoo(
            oid,
            auto_val
        )
    
    if payload.get("valid", False):
        room.is_validated()
        emit("closing", {"origin": cache.config["flask"]["address"]}, include_self=True, broadcast=True, to=str(context["rid"]))
        emit("validation", context,  broadcast=True, to="lobby")
    else:
        emit("validation-error", build_validation_error_payload(payload), include_self=True)
        
        
        
    
    

@scannettes.socketio.on("nullification")
@protected(auth_level="admin")
def nulify_inventory_products(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    room = lobby.rooms.get(int(context["rid"]))
    inventory: Inventory = room.data
    inventory.nullifier()
    emit("nullification", {"state": "ok", "data": context}, include_self=True, broadcast=True, to=str(context["rid"]))


@scannettes.socketio.on("suspend-rooms")
@protected(auth_level="admin")
def suspend_room(context):
    cache: Cache = current_app.cache
    config: Dict[str, Any] = cache.config
    lobby: Lobby = cache.lobby
    inventories: Inventories = cache.inventories
    deliveries: Deliveries = cache.deliveries
    
    for rid in context['rids']:
        lobby.delete_room(int(rid), inventories)
        emit("closing", {"origin": config["flask"]["address"]}, broadcast=True, to=str(rid))
        
    context["purchases"] = [pur.to_sel_tuple() for pur in deliveries.get_associable_purchases()]
    emit("suspend-rooms", {"state": "ok", "data": context}, include_self=True, broadcast=True, to="lobby")
    

@scannettes.socketio.on("rebase")
@protected(auth_level="admin")
def rebase(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    deliveries: Deliveries = cache.deliveries
    
    room = lobby.rooms.get(int(context["rid"]))
    oid = room.data.oid
    deliveries.recharge_purchase(oid)
    emit("rebase", {"state": "ok", "data": context}, include_self=True, broadcast=True, to=str(context["rid"]))