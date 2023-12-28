import json
from copy import deepcopy
from typing import Any, Dict, List, Tuple

from flask import current_app, url_for
from flask_socketio import emit, join_room

from cannettes_v2 import cannette
from cannettes_v2.authenticator import Authenticator
from cannettes_v2.decorators import protected
from cannettes_v2.odoo.lobby import Lobby
from cannettes_v2.odoo.odoo import Odoo
from cannettes_v2.odoo.deliveries import Deliveries
from cannettes_v2.odoo.inventories import Inventories
from cannettes_v2.tools.pdf import PDF
from cannettes_v2.tools.backup import Cache
from cannettes_v2.utils import Response
from cannettes_v2.utils import (
    format_error_client_message,
    get_passer,
    get_task_permission,
    standart_name,
    standart_object_name,
)

Cache = Dict[str, Any]
Payload = Dict[str, Any]



@cannette.socketio.on("message")
def log_message(msg):
    print(str(msg))
    
@cannette.socketio.on("initialization-call")
def initialize(context):
    """
    must return 
    
    app context for LOBBY
        > list of existing rooms
        > list of existing purcahases
        > list of existing categories
    """    
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    
    
    if context["instance"] == "lobby":
        context = {
            "origin": '/room',
            "rooms": [room.to_payload() for room in lobby.get_open_rooms()]
        }
        emit("lobby-initialization", context , include_self=True)
        
    elif context["instance"] == "room":
        rid = context["rid"]
        print(rid)
        print(lobby.__dict__)
        room = lobby.rooms.get(int(rid))
        print(room)
        context = {
            "room": room.to_payload(),
            "data": [product.to_payload(single_brcd=True) for product in room.data.products]
        }
        emit("room-initialization", context , include_self=True)
    


@cannette.socketio.on("admin-initialization-call")
@protected(auth_level="admin")
def admin_initialize(context):
    """
    must return 
    
    app context for LOBBY
        > list of existing rooms
        > list of existing purcahases
        > list of existing categories
    """  
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    deliveries: Deliveries = cache.deliveries

    if context["instance"] == "lobby":
        context = {
            "origin": f'admin/room',
            "rooms": [room.to_payload() for room in lobby.get_all_rooms()],
            "purchases": [pur.to_sel_tuple() for pur in deliveries.get_associable_purchases()],
            "categories": cache.inventories.categories,
        }
        emit("lobby-initialization", context , include_self=True)
    elif context["instance"] == "room":
        rid = context["rid"]
        room = lobby.rooms.get(rid)
        context = {
            "room": room.to_payload(),
            "data": [product.to_payload(single_brcd=True) for product in room.data.products]
        }        
        emit("room-initialization", context , include_self=True)
    

@cannette.socketio.on("add-rooms")
@protected(auth_level="admin")
def add_room(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    inventories: Inventories = cache.inventories
    deliveries: Deliveries = cache.deliveries
    erp = cache.config["odoo"]["erp"]
    
    adding_type = context.get("type", None)
    std_payload = {"state": "ok", "data": {"origin": "/room"}}
    adm_payload = {"state": "ok", "data": {"origin": "/admin/room"}}
    sel_payload = {"state": "ok", "data": {}}

    if adding_type == "purchase":
        oid = context.get("oid")
        purchase = deliveries.purchases.get(oid, None)
        context.update({"data": purchase})
        room = lobby.room_factory(context)
        rooms = [room.to_payload()]
        adm_payload["data"]["rooms"] = rooms
        std_payload["data"]["rooms"] = rooms
        sel_payload["data"]["purchases"] = [pur.to_sel_tuple() for pur in deliveries.get_associable_purchases()]
        emit("add-rooms", std_payload ,include_self=True, broadcast=True)
        emit("add-rooms-admin", adm_payload ,include_self=True, broadcast=True)
        emit("update-purchase-selector", sel_payload, include_self=True, broadcast=True)
    elif adding_type == "inventory":
        context.update({"catid": context.get("oid")})
        inventories.connect(**erp)
        invs = inventories.inventory_siblings_factory(**context)
        (shelf, stock) = lobby.room_sibling_factory(context, *invs)
        rooms = [shelf.to_payload(), stock.to_payload()] 
        adm_payload["data"]["rooms"] = rooms
        std_payload["data"]["rooms"] = rooms
        emit("add-rooms", std_payload ,include_self=True, broadcast=True)
        emit("add-rooms-admin", adm_payload ,include_self=True, broadcast=True)            
    else:
        payload = {"state": "err", "data": {"message": "Création de salon: quelque chose n'a pas marché."}}
        emit("message", payload, include_self=True)
    emit("close-creation-modal", include_self=True)


@cannette.socketio.on("del-rooms")
@protected(auth_level="admin")
def del_rooms(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    deliveries: Deliveries = cache.deliveries
    for rid in context["rids"]:
        lobby.delete_room(rid)
    sel_payload = {"state": "ok", "data": {"purchases": [pur.to_sel_tuple() for pur in deliveries.get_associable_purchases()]}}
    emit("del-rooms", {"state": "ok", "data": context})
    emit("update-purchase-selector", sel_payload, include_self=True, broadcast=True)
    
@cannette.socketio.on("reinit-rooms")
@protected(auth_level="admin")
def reinit_rooms(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    for rid in context["rids"]:
        lobby.reset_room(rid)
    emit("reinit-rooms", {"state": "ok", "data": context})
    


@cannette.socketio.on("generate-qrcodes")
def generate_qrcodes(context):
    cache: Cache = current_app.cache
    lobby: Lobby = cache.lobby
    payload = lobby.qrcode_iterator(context)
    
    pdf = PDF("P", "mm", "A4")
    output = pdf.generate_pdf(payload)
    emit("qrcodes-pdf", {"pdf": output})













# >>>>>>>>>>>>>>>>>>>>>>>>>> previous version >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


def task_permission_redirector(data, context) -> bool:
    permission = get_task_permission(data, context["suffix"])

    if permission == False:
        emit("task-access-denied", context, include_self=True)

    return permission


@cannette.socketio.on("message")
def handle_my_custom_event(msg):
    print(str(msg))


@cannette.socketio.on("authenticate")
def verify_loggin(context: Payload):
    authenticator = current_app.cache["config"]["authenticator"]
    users = current_app.users
    auth = Authenticator(**authenticator, **users).authenticate(**context)

    # resp = make_response(url_for("cannettes_bp.index_admin"))
    # resp.set_cookie("session", auth["token"])
    # return resp

    emit(
        "on-authentication",
        {"auth": auth, "redirect": url_for("cannettes_bp.index_admin")},
        include_self=True,
    )


@cannette.socketio.on("verify_connection")
def verify_logger(context):
    global data
    print(context)
    permission = False
    browser_id = context["browser_id"]
    suffix = context["suffix"]

    passer = get_passer(suffix)
    user_id = passer.get("id", None)
    token = passer.get("token", None)
    state = passer.get("state", None)

    roomID = context.get("roomID", None)
    if roomID:
        room = data["lobby"]["rooms"][roomID]
        room_state = room.status
    else:
        room_state = "open"

    if user_id in data["lobby"]["users"]["admin"].keys():
        user = data["lobby"]["users"]["admin"][user_id]
        if user.token == token and user.browser_id == browser_id:
            permission = True
            emit("grant_permission", {"permission": permission})

    if permission == False and room_state == "open":
        print("no permissions")
        emit("denied_permission", {"permission": permission}, include_self=True)

    elif roomID and permission == False and room_state == "close":
        print("access denied to closed room")
        emit(
            "no_access_redirection",
            {"permission": permission, "url": url_for("index")},
            include_self=True,
        )


@cannette.socketio.on("redirect")
def rredirect(context):
    global data

    id = context["id"]
    atype = context["type"]
    password = context["password"]
    browser = context["browser_id"]
    winWidth = context["winWidth"]
    suffix = context["suffix"]
    passer = get_passer(suffix)

    room = data["lobby"]["rooms"][id]
    room_token = room.token

    if data["config"].ACTIVATE_ROOM_PASSWORD is False:
        room.password = password

    if password == room.password:
        if suffix == "lobby" and atype == "purchase":
            # not admin purchase room
            emit(
                "go_to_room",
                {"url": url_for("get_purchase_room", id=id, room_token=room_token)},
            )

        elif suffix == "lobby" and atype == "inventory":
            # not admin inventory room
            emit(
                "go_to_room",
                {"url": url_for("get_inventory_room", id=id, room_token=room_token)},
            )

        else:
            # is admin
            user_id = passer.get("id", None)

            if user_id in data["lobby"]["users"]["admin"]:
                # check if user is active
                user = data["lobby"]["users"]["admin"][user_id]
                token = passer.get("token", None)
            else:
                user = None

            if (
                user
                and user.token == token
                and user.browser_id == browser
                and atype == "purchase"
            ):
                # OK go to purchase
                emit(
                    "go_to_room",
                    {
                        "url": url_for(
                            "get_purchase_room_admin",
                            id=id,
                            room_token=room_token,
                            user_id=user_id,
                            token=token,
                            state=room.status,
                            winWidth=winWidth,
                        )
                    },
                )

            elif (
                user
                and user.token == token
                and user.browser_id == browser
                and atype == "inventory"
            ):
                # OK go to iventory
                emit(
                    "go_to_room",
                    {
                        "url": url_for(
                            "get_inventory_room_admin",
                            id=id,
                            room_token=room_token,
                            user_id=user_id,
                            token=token,
                            state=room.status,
                            winWidth=winWidth,
                        )
                    },
                )

            else:
                # no user or not OK credentials, redirect non admin room
                if atype == "purchase":
                    emit(
                        "go_to_room",
                        {
                            "url": url_for(
                                "get_purchase_room", id=id, room_token=room_token
                            )
                        },
                    )

                else:
                    emit(
                        "go_to_room",
                        {
                            "url": url_for(
                                "get_inventory_room", id=id, room_token=room_token
                            )
                        },
                    )
    else:
        emit("access_denied", context, include_self=True)


@cannette.socketio.on("join_lobby")
def join_lobby():
    cache = current_app.cache
    print("joining lobby")
    context = {
        "room": [],
        "selector": [],
        "selector_inv": cache["odoo"]["inventory"]["type"],
    }

    for k in cache["lobby"]["rooms"].keys():
        record = cache["lobby"]["rooms"][k]
        context["room"].append(
            {
                "id": record.id,
                "name": standart_name(record.name, record.id),
                "status": record.status,
                "object_name": standart_object_name(
                    record.purchase.name, record.purchase.supplier_name
                ),
                "object_type": record.purchase.pType,
                "object_supplier": record.purchase.supplier_name,
                "date_oppening": record.oppening_date,
                "date_closing": record.closing_date,
            }
        )

    for k in cache["odoo"]["purchases"]["incoming"].keys():
        id = cache["odoo"]["purchases"]["incoming"][k].id
        name = cache["odoo"]["purchases"]["incoming"][k].name
        purchase_supplier = cache["odoo"]["purchases"]["incoming"][k].supplier_name

        if cache["odoo"]["purchases"]["incoming"][k].real:
            context["selector"].append(tuple((id, name + " - " + purchase_supplier)))

        else:
            context["selector"].append(tuple((id, name)))

    context["selector"] = sorted(
        context["selector"], key=lambda x: int(x[0]), reverse=True
    )

    emit("load_existing_lobby", context, include_self=True)


@cannette.socketio.on("join_room")
def joining_room(room):
    global data

    room = data["lobby"]["rooms"][room]
    name = room.name
    id = room.id
    room_state = room.status
    purchase = room.purchase.name
    purchase_supplier = room.purchase.supplier_name

    entry_records, queue_records, done_records = room.purchase.get_table_records()

    context = {
        "room_id": id,
        "room_name": name,
        "purchase_name": purchase,
        "purchase_supplier": purchase_supplier,
        "entries_records": entry_records,
        "queue_records": queue_records,
        "done_records": done_records,
        "scanned": room.purchase.scanned_barcodes,
        "new": room.purchase.new_items,
        "mod": room.purchase.modified_items,
    }

    emit("load_existing_room", context)


@cannette.socketio.on("create_room")
@protected(auth_level="admin")
def create_room(input):
    global data
    print("create room")

    if input["object_type"] == "inventory":
        # if envetory create inventory object
        config = data["config"]
        api = Odoo()
        api.connect(
            config.API_URL,
            config.SERVICE_ACCOUNT_LOGGIN,
            config.SERVICE_ACCOUNT_PASSWORD,
            config.API_DB,
            config.API_VERBOSE,
        )
        table = api.generate_inv_product_table(input["object_id"])
        input["object_id"] = api.create_inventory(input, data, table)

    room = Lobby().create_room(input, data)
    input["status"] = room.status
    input["users"] = room.users
    input["date_oppening"] = room.oppening_date
    input["supplier"] = room.purchase.supplier_name
    input["name"] = standart_name(input["name"], input["id"])
    input["object_name"] = standart_object_name(
        room.purchase.name, room.purchase.supplier_name
    )

    if room.purchase.process_status == None:
        room.purchase.build_process_tables()

    emit("add_room", input, broadcast=True, include_self=True)


@cannette.socketio.on("room_assembler")
def assembler(context):
    global data

    r1 = data["lobby"]["rooms"][context["ids"][0]]
    r2 = data["lobby"]["rooms"][context["ids"][1]]
    r = Lobby().room_assembler(r1, r2)
    Odoo().delete_purchase(r2.purchase.id, data, "inventory", "received")
    Lobby().delete_room(context["ids"][1], data)

    # emit to lobby, emit to room if anyone in
    emit(
        "broadcast_room_assembler",
        {"keep": context["ids"][0], "remove": context["ids"][1]},
        broadcast=True,
        include_self=True,
    )
    emit(
        "update_on_assembler",
        {"id": context["ids"][0]},
        broadcast=True,
        include_self=False,
    )


@cannette.socketio.on("del_room")
def del_room(id):
    global data

    Lobby().delete_room(id, data)


@cannette.socketio.on("reset_room")
def reset_room(id):
    global data

    Lobby().reset_room(id, data)


@cannette.socketio.on("generate-qrcode-pdf")
def generate_qrcode_pdf(context):
    global data

    content = Lobby().qrcode_iterator(context, data)
    pdf = PDF("P", "mm", "A4")
    output = pdf.generate_pdf(content["qrcodes"], content["captions"])

    emit("get-qrcode-pdf", {"pdf": output})


@cannette.socketio.on("image")
def image(data_image):
    global data

    # temporaly tracking fluidity of the flux
    # flux won't be further optimized, however frame interval each package is send can be modified
    config = data["config"]
    odoo = Odoo()
    odoo.connect(
        config.API_URL,
        config.SERVICE_ACCOUNT_LOGGIN,
        config.SERVICE_ACCOUNT_PASSWORD,
        config.API_DB,
        config.API_VERBOSE,
    )

    imageData = data_image["image"]
    room_id = data_image["id"]
    room = data["lobby"]["rooms"][room_id]
    context = room.image_decoder(imageData, room_id, room, odoo, data)

    if context["state"] == 1:
        join_room(room_id)
        emit(
            "move_product_to_queue",
            context,
            broadcast=True,
            include_self=True,
            to=room_id,
        )
        emit("change_color", broadcast=False, include_self=True, to=room_id)
        emit(
            "modify_scanned_item",
            context,
            broadcast=False,
            include_self=True,
            to=room_id,
        )

    elif context["state"] == 2:
        emit("change_color", broadcast=False, include_self=True, to=room_id)


@cannette.socketio.on("laser")
def laser(data_laser):
    global data

    config = data["config"]
    odoo = Odoo()
    odoo.connect(
        config.API_URL,
        config.SERVICE_ACCOUNT_LOGGIN,
        config.SERVICE_ACCOUNT_PASSWORD,
        config.API_DB,
        config.API_VERBOSE,
    )

    room_id = data_laser["id"]
    barcode = data_laser["barcode"]
    room = data["lobby"]["rooms"][room_id]
    context = room.laser_decoder(data_laser, room_id, barcode, room, odoo, data)

    if context["state"] == 1:
        join_room(room_id)
        emit(
            "move_product_to_queue",
            context,
            broadcast=True,
            include_self=True,
            to=room_id,
        )
        emit(
            "modify_scanned_laser_item",
            context,
            broadcast=False,
            include_self=True,
            to=room_id,
        )

    if context["state"] == 2:
        join_room(room_id)
        emit(
            "already-scanned-alert",
            context,
            broadcast=False,
            include_self=True,
            to=room_id,
        )


@cannette.socketio.on("update_table")
def get_update_table(context):
    global data

    room_id = context["roomID"]
    room = data["lobby"]["rooms"][room_id]
    context = room.purchase.update_table_on_edit(context)

    join_room(context["roomID"])
    emit(
        "broadcast_update_table_on_edit",
        context,
        broadcast=True,
        include_self=True,
        to=context["roomID"],
    )


@cannette.socketio.on("block-product")
def block_product(context):
    global data
    barcode = context["barcode"]
    room_id = context["roomID"]
    purchase = data["lobby"]["rooms"][room_id].purchase
    purchase.append_new_items(barcode)

    emit("broadcast-block-wrong-item", context, broadcast=True, include_self=True)


@cannette.socketio.on("del_item")
def get_del_item(context):
    global data
    print(context)
    permission = task_permission_redirector(data, context)

    if permission:
        room_id = context["roomID"]
        room = data["lobby"]["rooms"][room_id]
        room.purchase.delete_item(context["fromTable"], context["index"])

        join_room(context["roomID"])
        emit(
            "broadcasted_deleted_item",
            context,
            broadcast=True,
            include_self=True,
            to=context["roomID"],
        )


@cannette.socketio.on("suspending_room")
def suspend_room(context):
    global data

    permission = task_permission_redirector(data, context)

    if permission:
        room_id = context["roomID"]
        suffix = context["suffix"]

        passer = get_passer(suffix)
        user_id = passer.get("id", None)
        token = passer.get("token", None)

        if not user_id or not token:
            url = url_for("index")

        else:
            url = url_for("index_admin", id=user_id, token=token)

        Lobby().delete_room(room_id, data)

        context["url"] = url
        emit("broacasted_suspension", context, broadcast=True, include_self=True)


@cannette.socketio.on("finishing_room")
def finish_room(context):
    global data

    room_id = context["roomID"]
    suffix = context["suffix"]
    passer = get_passer(suffix)
    user_id = passer.get("id", None)
    token = passer.get("token", None)
    object_type = passer.get("type", None)

    if not user_id or not token:
        context["url"] = url_for("index")

    else:
        context["url"] = url_for("index_admin", id=user_id, token=token)

    room = data["lobby"]["rooms"][room_id]
    room.update_status("received", "finished", "close", object_type, data)

    emit("broacasted_finish", context, broadcast=True, include_self=True)


@cannette.socketio.on("recharging_room")
def recharge_room(context):
    global data

    permission = task_permission_redirector(data, context)
    config = data["config"]
    odoo = Odoo()
    odoo.connect(
        config.API_URL,
        config.SERVICE_ACCOUNT_LOGGIN,
        config.SERVICE_ACCOUNT_PASSWORD,
        config.API_DB,
        config.API_VERBOSE,
    )

    if permission:
        room_id = context["roomID"]
        purchase = data["lobby"]["rooms"][room_id].purchase
        odoo.recharge_purchase(purchase, data)
        emit("reload-on-recharge", context, broadcast=False, include_self=True)
        emit("broadcast-recharge", context, broadcast=True, include_self=False)


@cannette.socketio.on("nullification")
def nullify(context):
    global data

    room = data["lobby"]["rooms"][context["roomID"]]
    room.purchase.nullifier()

    context["mod"] = room.purchase.modified_items
    context["new"] = room.purchase.new_items
    emit("broadcast-nullification", context, broadcast=True, include_self=True)


@cannette.socketio.on("validation-purchase")
def validate_purchase(context):
    global data

    permission = task_permission_redirector(data, context)
    config = data["config"]
    odoo = Odoo()
    odoo.connect(
        config.API_URL,
        config.SERVICE_ACCOUNT_LOGGIN,
        config.SERVICE_ACCOUNT_PASSWORD,
        config.API_DB,
        config.API_VERBOSE,
    )

    if permission:
        print("____validation process______")

        passer = get_passer(context["suffix"])
        room = data["lobby"]["rooms"][context["roomID"]]
        purchase = room.purchase
        object_type = passer.get("type", None)

        if object_type == "purchase":
            state = odoo.post_purchase(purchase, data, context["autoval"])
        else:
            state = odoo.post_inventory(purchase, data, context["autoval"])

        if state["validity"]:
            room.update_status("received", "verified", "done", object_type, data)

            user_id = passer.get("id", None)
            token = passer.get("token", None)
            if not user_id or not token:
                context["url"] = url_for("index")
            else:
                context["url"] = url_for("index_admin", id=user_id, token=token)
            emit("close-room-on-validation", context)

        else:
            msg = format_error_client_message(state["errors"])
            emit(
                "close-test-fail-error-window",
                {"errors": msg, "failed": state["failed"], "roomID": context["roomID"]},
            )
