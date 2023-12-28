

var initialized = false;
const socket = io.connect(config.address);





socket.on("connect", function() {
    if (!initialized) {
        initialized = true;
        socket.emit('admin-initialization-call', {"instance": "lobby"});
    }
});

socket.on("lobby-initialization", function(context) {
    let base = context.origin;
    addOptions(context.purchases, "purchases");
    addOptions(context.categories, "categories");
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
    addOptions(data.purchases, "purchases");
});

socket.on("add-rooms-admin", function(context) {
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
    new MsgFactory("ok", "Salons crées");
});

socket.on("close-creation-modal", function() {
    creationModal();
});

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
    new MsgFactory(state, "<strong>Suppression</strong> : Salons supprimés");
});

socket.on("reinit-rooms", function(context) {
    const state = context.state;
    new MsgFactory(state, "<strong>Réinitialisation</strong> : Salons Réinitialisés");
});

socket.on("qrcodes-pdf", function(context) {
    let buffer = context.pdf;
    let pdfWindow = window.open("");
    pdfWindow.document.write(
        "<iframe width='100%' height='100%' src='data:application/pdf;base64, " +
        encodeURI(buffer) + "'></iframe>"
    );
});



function unwrap_or_else(payload, errMsg) {
    if (payload.state == "err") {
        new MsgFactory("err", errMsg);
        return null;
    } else {
        return payload.data;
    }
}


////////////////////////////////////////////// room-table content objects

class RoomFactory {
    constructor(payload) {
        const table = document.getElementById("room-table");
        if (payload === "placeholder") {
            table.appendChild(this.placeHolder())
        } else {
            let frame = this.buildRoom(payload);
            console.log(frame);
            table.appendChild(frame);
        }
    }

    buildRoom(payload) {
        let frame = this.buildFrame(payload);

        frame.appendChild(this.buildCheckBox())
        frame.appendChild(this.buildSeparator());
        frame.appendChild(this.buildCell(this.defaultName(payload), ["grid-cell", "padding", "long", "rname"]));
        frame.appendChild(this.buildSeparator());
        frame.appendChild(this.buildCell(payload.display_name, ["grid-cell", "padding", "pname"]));
        frame.appendChild(this.buildSeparator());
        frame.appendChild(this.buildCell(this.translateState(payload.state), ["grid-cell", "padding", "long", "pstate"]));
        frame.appendChild(this.buildSeparator());
        if (payload.state != "done") {
            frame.appendChild(this.buildCell(payload.creating_date, ["grid-cell", "padding", "long", "pdate"]));
        } else {
            frame.appendChild(this.buildCell(payload.closing_date, ["grid-cell", "padding", "long", "pdate"]));
        }
        frame.appendChild(this.buildSeparator());
        frame.appendChild(this.buildPassCell());
        frame.appendChild(this.buildAccessBtn(payload.origin, payload.token, payload.rid));
        return frame;
    }

    buildFrame(payload) {
        let elm = document.createElement("div");
        elm.classList.add("purchase", payload.state);
        elm.setAttribute("state", payload.state);
        elm.setAttribute("sibling", payload.sibling);
        elm.setAttribute("otype", payload.type);
        elm.setAttribute("oid", payload.oid);
        elm.setAttribute("rid", payload.rid);
        elm.setAttribute("token", payload.token);
        return elm;
    }

    buildCheckBox() {
        let elm = document.createElement("div");
        elm.classList.add("grid-cell", "check");

        let inp = document.createElement("input");
        inp.classList.add("selectBox");
        inp.setAttribute("type","checkbox");

        elm.appendChild(inp);
        return elm;
    }

    buildCell(text, classes) {
        let elm = document.createElement("div");
        elm.innerText = text;
        for (var cls of classes) {
            elm.classList.add(cls);
        }
        return elm;
    }

    buildPassCell() {
        let elm = document.createElement("div");
        elm.classList.add("grid-cell", "rpass");

        let inp = document.createElement("input");
        inp.setAttribute("type", "password");
        inp.setAttribute("autocomplete", "off");
        inp.setAttribute("placeholder", "Mot de passe...");

        elm.appendChild(inp);
        return elm;
    }

    buildAccessBtn(origin, token, rid) {
        let url = origin+"/"+token+"?rid="+rid;
        let elm = document.createElement("div");
        elm.classList.add("grid-cell-btn", "raccess");

        let redirector = document.createElement("a");
        redirector.setAttribute("href", url)

        let btn = document.createElement("button");

        let iframe = document.createElement("i");
        iframe.classList.add("arrow", "right");

        btn.appendChild(iframe);
        redirector.appendChild(btn)
        elm.appendChild(redirector);
        return elm;
    }

    buildSeparator() {
        let elm = document.createElement("div");
        elm.classList.add("separator");
        return elm;
    }

    placeHolder() {
        let elm = document.createElement("div");
        elm.classList.add("placeholder");

        let text = document.createElement("p");
        text.innerText = "Aucun Salon";

        elm.appendChild(text);
        return elm;
    }

    translateState(state) {
        if (state == "open") {
            return "Ouvert";
        } else if (state == "close") {
            return "Fermé";
        } else if (state == "done") {
            return "Fini";
        }
    }

    defaultName(payload) {
        if (payload.name != "") {
            return payload.name;
        }
        let rid = payload.rid;
        return "Salon n° " + rid;
    }
}

function rmPlaceholder() {
    const table = document.getElementById("room-table");
    let placeholder = table.getElementsByClassName("placeholder");
    if (placeholder.length > 0) {
        placeholder[0].remove();
    }
}

function addPlaceholder() {
    const table = document.getElementById("room-table");
    let purchases = table.getElementsByClassName("purchase");
    let placeholder = table.getElementsByClassName("placeholder");
    if (purchases.length === 0 & placeholder.length === 0) {
        new RoomFactory("placeholder");
    }
}




//////////////////////////////////////////////////////////////////////////////////////////////////////

function getSelectedOptions(type) {
    const purchase = document.getElementById('purchases');
    const inventory = document.getElementById('categories');
    let object_id;
    let object_name;
    if (type == 'purchase') {
        object_id = parseInt(purchase.options[purchase.selectedIndex].value);
        object_name = purchase.options[purchase.selectedIndex].innerHTML;
    } else {
        object_id = parseInt(inventory.options[inventory.selectedIndex].value);
        object_name = inventory.options[inventory.selectedIndex].innerHTML;
    }
    return [object_id, object_name]
}

function getPType() {
    let check =  document.getElementById('pType-check').checked;
    if (check) {
        var pType = 'inventory';
    } else {
        var pType = 'purchase';
    }
    return pType
}


function createRoom() {
    const roomName = document.getElementById('room-name');
    const roomPassword = document.getElementById('room-password');
    const infoContainer = document.getElementById("creation-info");
    let type = getPType();
    let [ObjectId, _] = getSelectedOptions(type);
    let name = roomName.value;
    let password = roomPassword.value;
    socket.emit("add-rooms", {"type": type, "oid": ObjectId, "name": name, "password": password});
    infoContainer.innerText = "Création en cours...";
}

function delSelRooms() {
    let selected = getSelRids();
    if (selected.length == 0) {
        new MsgFactory("err", "<strong>Erreur lors de la suppression</strong> : Aucun salon sélectionné");
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
    socket.emit("del-rooms", {"rids": selected});
    CloseCModal();
}

function reInitSelRooms() {
    let selected = getSelRids();
    if (selected.length == 0) {
        new MsgFactory("err", "<strong>Erreur lors de la réinitialisation</strong> : Aucun salon sélectionné");
    } else {
        openCModal(
            "Réinitialisation ?",
            "Confirmer la réinitialisation des salons ?",
            "initRooms()",
      );
    }
}

function initRooms() {
    let selected = getSelRids();
    socket.emit("reinit-rooms", {"rids": selected});
    CloseCModal();
}

function GenerateQrCode() {
    let selected = getSelRids();
    if (selected.length == 0) {
        new MsgFactory("err", "<strong>Erreur lors de la generation des qrcodes</strong> : Aucun salon sélectionné");
    } else {
        let curUrl = window.location.href;
        let origin = new URL(curUrl).origin;
        console.log(origin);
        socket.emit("generate-qrcodes", {"rids": selected, "origin": origin});
    }
}




function getSelRids() {
    let selected = [];
    const rooms = document.getElementsByClassName("purchase");
    for (var room of rooms) {
        let checked = room.getElementsByClassName("selectBox")[0].checked;
        if (checked) {
            selected.push(parseInt(room.getAttribute("rid")))
        }
    }
    return selected;
}

function handle0SelCase() {

}


///////// GENERATE OPTIONS CHOICES

function addRooms(rooms, base, objectId) {
    const table = document.getElementById(objectId);
    for (var room of rooms) {
        room.origin = base;
        new RoomFactory(room);
    }
}

function addOptions(inputs, objectId) {
    const selector = document.getElementById(objectId);
    selector.innerHTML = "";
    for (var option of inputs) {
        let name = option[1].toString();
        let id = option[0].toString();
        selector.add(createOption(name, id), null);
    }
}

function createOption(text, value) {
    let option = document.createElement('option');
    option.value = value;
    option.text = text;
    return option;
}

//////////// SWITCH INV/PUR

function creationModal() {
    const page = document.getElementById("html");
    const modal = document.getElementById("creation-modal");
    const switcher = document.getElementById("pType-check");
    const purContainer = document.getElementById('purchase-container');
    const invContainer = document.getElementById('inv-container');
    const roomName = document.getElementById('room-name');
    const roomPassword = document.getElementById('room-password');
    const purchase = document.getElementById('purchases');
    const inventory = document.getElementById('categories');
    const infoContainer = document.getElementById("creation-info");

    let display = modal.style.display;
    if (display != "flex") {
        modal.style.top = (window.scrollY - 5).toString() + 'px';
        modal.style.display = "flex";
        infoContainer.innerText = "";
        switcher.checked = false;
        purContainer.style.display = 'flex';
        invContainer.style.display = 'none';
        page.style.overflowY = 'hidden';
    } else {
        modal.style.display = "none";
        roomName.value = '';
        roomPassword.value = '';
        infoContainer.innerText = "";
        purchase.selectedIndex = 0;
        inventory.selectedIndex = 0;
        switcher.checked = false;
        page.style.overflowY = 'visible';
    }
}

function switchContainer() {
    const switcher = document.getElementById("pType-check");
    const purContainer = document.getElementById('purchase-container');
    const invContainer = document.getElementById('inv-container');
    if (switcher.checked) {
        purContainer.style.display = 'none';
        invContainer.style.display = 'flex';
    } else {
        purContainer.style.display = 'flex';
        invContainer.style.display = 'none';
    }
}


//////////////////////////////////////////// MSG BOX


function closeMsg(elm) {
    let box = elm.parentElement.parentElement;
    box.remove();
}

///////////////////////////////////////// SORTING

function tableSort(elm) {
    let selected = elm.getElementsByClassName("order")[0];
    new TableSorter(selected);
}


class TableSorter {
    constructor(sel) {
        let symbols = {"neu": "-", "asc": "▼", "des": "▲"};
        let reversedSymbols = {"-": "neu", "▼": "asc", "▲": "des"};
        let orders = {"neu": "asc", "asc": "des", "des": "asc"};


        let currentSelector = sel.id;
        let currentSortingState = reversedSymbols[sel.innerText];
        let nextSortingState = orders[currentSortingState];
        let nextSymbol = symbols[nextSortingState];

        let [nodesRef, valuesRef] = this.collectNodes(currentSelector);
        let sorted = this.sort(nextSortingState, valuesRef);
        this.inject(sorted, nodesRef);
        this.modifySortingStates(currentSelector, nextSymbol);
    }


    collectNodes(selid) {
        let stateValues = {"open": 1, "close": 2, "done": 3};
        const table = document.getElementById("room-table");
        let nodes = table.getElementsByClassName("purchase");

        let nodesRef = {};
        let valuesRef = [];

        Array.from(nodes).forEach( function(node) {
            let rid = node.getAttribute("rid");
            let refcell = node.getElementsByClassName(selid.split('-')[0])[0];
            nodesRef[rid] = node;
            if (selid === "date-order") {
                let date = new Date(refcell.innerText);
                valuesRef.push([date, rid]);
            } else if (selid === "state-order") {
                let stateVal = stateValues[node.getAttribute("state")];
                valuesRef.push([stateVal, rid]);
            } else {
                let text = refcell.innerText;
                valuesRef.push([text, rid]);
            }
        });
        return [nodesRef, valuesRef];
    }

    sort(order, valuesRef) {
        let sorted;
        if (order == "asc") {
            console.log("ascending ordering");
            sorted = valuesRef.sort(([a,b], [c,d]) => {
                if (a > c)
                    return 1;
                if (a < c)
                    return -1;
                return 0;
            });

        } else if (order == "des") {
            console.log("descending ordering");
            sorted = valuesRef.sort(([a,b], [c,d]) => {
                if (a > c)
                    return -1;
                if (a < c)
                    return 1;
                return 0;
            });
        }
        return sorted;
    }

    inject(valuesRef, nodesRef) {
        const table = document.getElementById("room-table");
        table.innerHTML = "";
        for (var [v, rid] of valuesRef) {
            let node = nodesRef[rid];
            table.appendChild(node);
        }
    }

    modifySortingStates(selid, next) {
        let selector = document.getElementById(selid);
        let others = document.getElementsByClassName("order");
        selector.innerHTML = next;
        Array.from(others).forEach( function(node) {
            if (node.id != selid) {
                node.innerHTML = "-";
            } 
        });
    }
}


////////// SEARCH BAR

function searchRoom(event) {
    let input = document.getElementById("searchbar").value.toLowerCase();
    if (input == "") {
        resetSearch();
    } else {
        filterRooms(input);
    }
}

function filterRooms(input) {
    const table = document.getElementById("room-table");
    let nodes = table.getElementsByClassName("purchase");
    for (node of nodes) {
        let rname = node.getElementsByClassName("rname")[0].innerText.toLowerCase();
        let pname = node.getElementsByClassName("pname")[0].innerText.toLowerCase();
        if (rname.includes(input) || pname.includes(input)) {
            console.log(input, pname, rname);
            node.style.display = "grid";
        } else {
            node.style.display = "none";
        }
    }  
}

function resetSearch() {
    const table = document.getElementById("room-table");
    document.getElementById("searchbar").value = "";
    let nodes = table.getElementsByClassName("purchase");
    for (node of nodes) { node.style.display = "grid" };
}


//////////////////////// MESSAGE GENERATION

class MsgFactory {
    constructor(mtype, msg) {
        const container = document.getElementById("msg-box");

        let frame = this.buildFrame(mtype);
        frame.appendChild(this.buildSymbol(mtype));
        frame.appendChild(this.buildMsg(msg));
        frame.appendChild(this.buildExit());

        container.appendChild(frame);
    }


    buildFrame(mtype) {
        let frame = document.createElement("div");
        frame.classList.add(mtype, "msg-container");
        return frame;
    }

    buildSymbol(mtype) {
        let elm = document.createElement('img');
        elm.classList.add("msg-symbol","msg-comp");
        elm.setAttribute("src","../static/misc/"+mtype+".png");
        return elm;
    }

    buildMsg(msg) {
        let elm = document.createElement("p");
        elm.classList.add("msg", "msg-comp");
        elm.innerHTML = msg;
        return elm;
    }

    buildExit() {
        let elm = document.createElement("div");
        elm.classList.add("quit-container");
        
        let btn = document.createElement("button");
        btn.classList.add("msg-quit", "msg-comp");
        btn.setAttribute("onclick", "closeMsg(this)");
        btn.innerText = "x";

        elm.appendChild(btn);
        return elm;   
    }
}

///////////////////////////////// CONFIRMATION MODAL

function openCModal(headerMsg, bodyMsg, closeFunc) {
    const page = document.getElementById('html');
    const modal = document.getElementById("confirmation-modal");
    const header = document.getElementById('heading-message');
    const message = document.getElementById('content-message');
    const button = document.getElementById('accept-confirmation');

    window.scrollTo(0, window.scrollY); 
    modal.style.top = (window.scrollY - 5).toString() + 'px';
    modal.style.display = 'flex';
    page.style.overflowY = 'hidden';
    header.innerHTML = headerMsg;
    message.innerHTML = bodyMsg;
    button.setAttribute('onclick', closeFunc);
}

function CloseCModal() {
    document.getElementById('confirmation-modal').style.display = 'none';
    document.getElementById('html').style.overflowY = 'visible';
    document.getElementById('cancel-confirmation').hidden = false;
    document.getElementById('accept-confirmation').hidden = false;
}