// INIT
var initialized = false;
const admin = isAdmin();
const socket = io.connect(config.address);

var rPass = config["activate_room_password"] ?? false;


// SOCKETIO EVENTS

socket.on("connect", function() {
    if (!initialized) {
        initialized = true;
        if (admin) {
            socket.emit('admin-initialization-call', {"instance": "lobby"});
        } else {
            socket.emit('initialization-call', {"instance": "lobby"});
        }
        
    }
});

socket.on("lobby-initialization", function(context) {
    let base = context.origin;

    if (admin) {
        new MenuFactory();
        addOptions(context.purchases, "purchases");
        addOptions(context.categories, "categories");
        if (!rPass) {
            document.getElementById("room-password").readOnly = true;
        }
    } else {
        document.getElementById("confirmation-modal").remove();
        document.getElementById("creation-modal").remove();
    }

    if (context.rooms.length > 0) {
        addRooms(context.rooms, base, "room-table");
    } else {
        new RoomFactory("placeholder");
    }
});



socket.on("update-purchase-selector", function(context) {
    let data = unwrap_or_else(context, "erreur 0");
    if (data === null) {
        return;
    }
    if (admin) {
        addOptions(data.purchases, "purchases");
    }
});



/// CLOSE MODAL
socket.on("close-modal", function(context) {
    CloseCModal();
    waitingConf("close");
})


socket.on("closing", function(context) {
    const payloadState = context.state;
    const data = context.data;

    if (data.assembling) {
        document.getElementById(data.rid).remove();
        document.getElementById(data.sibling).remove();
        new RoomFactory(data.room);
        new MsgFactory("msg-box", payloadState, "<strong>Assemblement des inventaire :</strong> "+ data.room.display_name, true, 3000, 1000)
    } else {
        let room = document.getElementById(data.rid);
        room.setAttribute("state", "close");
        room.classList.replace("open", "close");
        new MsgFactory("msg-box", payloadState, "<strong>Fermeture :</strong> "+ data.room.display_name, true, 3000, 1000);
    }
});

socket.on("validation", function(context) {
    let room = document.getElementById(context.rid);
    room.setAttribute("state", "done");
    room.classList.replace("close", "done");
    new MsgFactory("msg-box", payloadState, "<strong>Validation :</strong> "+ data.room.display_name, true, 3000, 1000);
});

// CREATE ROOM CALLBACK
function createRoom() {
    const roomName = document.getElementById('room-name');
    const roomPassword = document.getElementById('room-password');
    let type = getPType();
    let [ObjectId, _] = getSelectedOptions(type);
    let name = roomName.value;
    let password = roomPassword.value;
    socket.emit("add-rooms", {"type": type, "oid": ObjectId, "name": name, "password": password});
    WaitingCreation("open");
}


socket.on("add-rooms", function(context) {
    let data = unwrap_or_else(context, "erreur 1");
    if (data === null) {
        return;
    }

    rmPlaceholder();
    let rooms = data.rooms;
    let base = data.origin;
    for (room of rooms) {
        room.origin = base;
        new RoomFactory(room);    
    }
    new MsgFactory("msg-box", "ok", "<strong>Création de salon: </strong> "+ rooms[0].display_name, true, 5000, 1000);
});

socket.on("close-creation-modal", function() {
    creationModal();
});


// DEL ROOMS CALLBACKS
function delSelRooms() {
    let selected = getSelRids();
    if (selected.length == 0) {
        new MsgFactory("msg-box", "err", "<strong>Erreur lors de la suppression</strong> : Aucun salon sélectionné", true, 3000, 1000);
    } else {
        openCModal(
            "Suppression ?",
            "Confirmer la suppression des salons ?",
            "delRooms()",
      );
    }
}

function delRooms() {
    let selected = getSelRids();
    waitingConf("open");
    socket.emit("del-rooms", {"rids": selected});
}


socket.on("del-rooms", function(context) {
    const rooms = document.getElementById("room-table").getElementsByClassName("purchase");
    const state = context.state;
    let rids = context.data.rids;
    Array.from(rooms).forEach( function(room) {
        let rid = parseInt(room.getAttribute("rid"));
        console.log(rid);
        if (rids.includes(rid)) {
            console.log(rid, "included");
            room.remove();
        }
    });
    addPlaceholder();
    new MsgFactory("msg-box", state, "<strong>Suppression</strong> : Salons supprimés");
});


// SUSPEND ROOM AGAIN CALLBACK
function confSuspension() {
    let selected = getSelRids();
    if (selected.length == 0) {
        new MsgFactory("msg-box", "err", "<strong>Erreur lors de la suspension</strong> : Aucun salon sélectionné");
    } else {
        openCModal(
            "Suspendre ?",
            "Confirmer la suspension des salons ?",
            "suspendRooms()",
      );
    }
}

function suspendRooms() {
    let selected = getSelRids();
    waitingConf("open");
    socket.emit("suspend-rooms", {"rids": selected});
}

socket.on("suspend-rooms", function(context) {
    const state = context.state;
    new MsgFactory("msg-box", state, "<strong>"+context.data.rids.length+" Salons suspendus</strong>", true, 3000, 1000);
    for (rmrid of context.data.rids) {
        document.getElementById(rmrid).remove();
    }
    addPlaceholder();
    addOptions(context.data.purchases, "purchases");
    new MsgFactory("msg-box", "ok", "<strong>Suspenssion de Salons: </strong> ", true, 5000, 1000);
});



// QR CODE GENERATION CALLBACK
function GenerateQrCode() {
    let selected = getSelRids();
    if (selected.length == 0) {
        new MsgFactory("msg-box", "err", "<strong>Erreur lors de la generation des qrcodes</strong> : Aucun salon sélectionné");
    } else {
        let curUrl = window.location.href;
        let origin = new URL(curUrl).origin;
        console.log(origin);
        socket.emit("generate-qrcodes", {"rids": selected, "origin": origin});
    }
}

socket.on("qrcodes-pdf", function(context) {
    let buffer = context.pdf;
    let pdfWindow = window.open("");
    pdfWindow.document.write(
        "<iframe width='100%' height='100%' src='data:application/pdf;base64, " +
        encodeURI(buffer) + "'></iframe>"
    );
});