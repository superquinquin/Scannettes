

var initialized = false;
const params = new URLSearchParams(window.location.search);
const rid = params.get("rid");
const admin = isAdmin();
var state;
var type;
var scanned = [];
var autoval;

const socket = io.connect(config.address);

socket.on("connect", function() {
    if (!initialized) {
        initialized = true;
        if (admin) {
            socket.emit('admin-initialization-call', {"instance": "room", "rid": parseInt(rid)});
        } else {
            socket.emit('initialization-call', {"instance": "room", "rid": parseInt(rid)});
        }
    }
});

socket.on("room-initialization", function(context) {
    console.log(context);
    state = context.room.state;
    type = context.room.type;
    autoval = setAutoval();
    new MenuFactory(context.room);
    addProducts(context.data);
    addPlaceholder("initial");
    addPlaceholder("done");
    addPlaceholder("lmmodal");

    if (state != "open") {
        openAllCollapsers();
    }

});


// 
function setAutoval() {
    if (type === "inventory") {
        return config["odoo_auto_inventory_validation"] ?? false;
    } else if (type === "purchase") {
        return config["odoo_auto_purchase_validation"] ?? false;
    }
}

//////////////////////////////  COLLAPSING BLOCKS

function openCollapser(elm) {
    elm.classList.toggle("active");
    var content = elm.nextElementSibling;
    if (content.style.display == 'flex') {
        content.style.display = 'none';
    } else {
        content.style.display = 'flex';
    }
}

function openAllCollapsers() {
    const collapser = document.getElementsByClassName("collaps-block");
    for (var i = 0; i < collapser.length; i++) {
        openCollapser(collapser[i]);
    }
}

///// scroll to top

// window.addEventListener('scroll', appearToTop());

window.addEventListener('scroll', function() {
    appearToTop()
});

function appearToTop() {
    let limit = 500;
    const toTop = document.getElementById("toTop");
    if (window.scrollY >= limit && toTop.style.display == "none") {
        toTop.style.display = "flex";
    } else if (window.scrollY < limit && toTop.style.display == "flex") {
        toTop.style.display = "none";
    }
}

function scrolltop() {
    window.scrollTo(0, 0);
  }



/// CLOSE MODAL
socket.on("close-modal", function(context) {
    CloseCModal();
    waitingConf("close");
})



////// Reinit

function confReInit() {
    openCModal(
        "Réinitialisation ?",
        "Réinitialiser les données du salon ?",
        "reInitialize()",
    );
}

function reInitialize() {
    waitingConf("open");
    socket.emit("reinit-room", {"rid": rid});
}

socket.on("reinit-room", function(context) {
    const roomState = context.state;
    if (roomState === "ok") {
        new MsgFactory("msg-box", state, "<strong>Salon Réinitialisé</strong>", true, 3000, 1000);
        window.location.reload();
    } else {
        new MsgFactory("msg-box", state, "<strong>Erreur lors de la Réinitialisation</strong>", true, 3000, 1000);
    }
});


/////// REBASE

function confRebase() {
    openCModal(
        "Recharger ?",
        "Recharger la commande depuis Odoo?",
        "rebase()",
    );
}

function rebase() {
    waitingConf("open");
    socket.emit("rebase", {"rid": rid});
}

socket.on("rebase", function(context) {
    const roomState = context.state;
    if (roomState === "ok") {
        new MsgFactory("msg-box", state, "<strong>Commande rechargée</strong>", true, 3000, 1000);
        window.location.reload();
    } else {
        new MsgFactory("msg-box", state, "<strong>Erreur lors du rechargement de la Commande</strong>", true, 3000, 1000);
    }
});

///// NULIFICATION

function confNullify() {
    openCModal(
        "Nullification ?",
        "Nullifier les quantités des produits non scannés ?",
        "nullify()",
    );
}

function nullify() {
    waitingConf("open");
    socket.emit("nullification", {"rid": rid});
}

socket.on("nullification", function(context) {
    const roomState = context.state;
    if (roomState === "ok") {
        new MsgFactory("msg-box", state, "<strong>Données nullifiés</strong>", true, 3000, 1000);
        window.location.reload();
    } else {
        new MsgFactory("msg-box", state, "<strong>Erreur lors de la nullification</strong>", true, 3000, 1000);
    }
})

////// DEL PORDUCTS

function delConf(containerId) {
    const container = document.getElementById(containerId);
    let nodes = container.getElementsByClassName("product");
    let names = getSelectedNodesDisplayNames(nodes);
    if (names.length == 0) {
        new MsgFactory("msg-box", "err", "<strong>Erreur suppression</strong> : Aucun produit selectionné", true, 3000, 1000);
    } else {
        openCModal(
            "Suppression ?",
            "Confirmer la suppression des produits ?",
            "delProducts('"+containerId+"')",
            formatListing(names)
      );
    }
}

function delProducts(containerId) {
    const container = document.getElementById(containerId);
    let nodes = container.getElementsByClassName("product");
    let uuids = getSelectedNodesUUID(nodes);
    waitingConf("open");
    socket.emit("delete-products", {"from": containerId, "rid": rid, "uuids": uuids});
}

socket.on("delete-products", function(context) {
    console.log(context.uuids);
    for (uuid of context.uuids) {
        document.getElementById(uuid).remove();
    }
    new MsgFactory("msg-box", "ok", "<strong>"+context.uuids.length+" produits supprimés</strong>", true, 3000, 1000);
    addPlaceholder(context.from);
});


function getSelectedNodesUUID(nodes) {
    let uuids = [];
    for (node of nodes) {
        let box = node.getElementsByClassName("pcheck")[0];
        if (box.checked) {
            uuids.push(node.getAttribute("uuid"));
        }
    }
    return uuids;
}

function getSelectedNodesDisplayNames(nodes) {
    let names = [];
    for (node of nodes) {
        let box = node.getElementsByClassName("pcheck")[0];
        if (box.checked) {
            names.push(node.getAttribute("name") +" ("+node.getAttribute("barcodes")+")");
        }
    }
    return names;
}


////// CLOSE & validate ROOM

function confClosing() {
    var header;
    if (type === "purchase") {
        header = "Terminer la réception ?";
    } else {
        header = "Terminer l'inventaire ?";
    }

    openCModal(
        header,
        "Confirmer la fermeture du salon ?",
        "closeRoom()",
  );
}

function confValidate() {
    var header;
    if (type === "purchase") {
        header = "Valider la réception ?";
    } else {
        header = "Valider l'inventaire ?";
    }

    openCModal(
        header,
        "Confirmer la validation du salon ?",
        "validateRoom()",
  );
  if (autoval) {
    showAutoval("open");
  } 
}

function closeRoom() {
    waitingConf("open");
    socket.emit("closing", {"rid": rid});
}

function validateRoom() {
    waitingConf("open");
    let autoval = getAutoValValue();
    socket.emit("validation", {"rid": rid, "autoval": autoval});
}

socket.on("closing", function(context) {
    if (admin) {
        window.location.replace(context.origin+"/admin/lobby");
    } else {
        window.location.replace(context.origin+"/lobby");
    }
});

socket.on("validation-error", function(context) {
    new MsgFactory("msg-box","err", "<strong>Erreur lors du processus de validation...</strong>", true, 5000, 1000);
    waitingConf("close");
    lockwindow();
    openCModal(
        "Erreur...",
        context.error_message,
        "CloseCModal()",
        formatListing(context.faulty_products)
    );
});

/////// PRODUCT ACTIONS 
//ok
function correctProductQty(elm) {
    let product = elm.parentNode.parentNode;
    let uuid = product.getAttribute("uuid");
    let state = product.getAttribute("state");
    socket.emit("modify-product",{"uuid": uuid, "original_state": state, "rid": rid, "has_modifications": false, "modifications": {}});
}

function rmFromScanned(uuid) {
    let container = document.getElementById("scanned-products");
    let products = container.getElementsByClassName("product");
    for (product of products) {
        let productUuid = product.getAttribute("uuid");
        if (uuid === productUuid) {
            product.remove();
            break
        }
    }
}

// modify
function OpenModification(elm) {
    let product = elm.parentNode.parentNode;
    let conf = product.getElementsByClassName("apply-mod")[0];
    let input = product.getElementsByClassName("product-mod-input")[0];
    if (input.style.display === "none") {
        conf.style.display = "flex";
        input.style.display = "flex";
        input.focus();
    } else {
        conf.style.display = "none";
        input.style.display = "none";
    }
}

function keyModify(e, elm) {
    // enable modifyProductQty callback from key "enter" on input field
    if (e.key === "Enter") {
        let product = elm.parentNode;
        let btn = product.getElementsByClassName("apply-mod")[0].firstChild;
        modifyProductQty(btn);
        giveLaserFocus();
    }
}

function modifyProductQty(elm) {
    let product = elm.parentNode.parentNode;
    let inputfield = product.getElementsByClassName("product-mod-input")[0];
    let input = inputfield.value;
    let uuid = product.getAttribute("uuid");
    let state = product.getAttribute("state");

    let okChars = checkIntChars(input);
    let okrange = parseFloat(input) < 200;
    let okzeros = input[0] === "0" && input[1] != ".";
    if (okChars &&  okrange && !okzeros) {
        socket.emit("modify-product",{"uuid": uuid, "original_state": state, "rid": rid, "has_modifications": true, "modifications": {"qty_received": input}});
        OpenModification(product.getElementsByClassName("apply-mod")[0].getElementsByTagName("button")[0]);
        giveLaserFocus();
    } else if (!okChars) {
        new MsgFactory("msg-box", "err", "<strong>La quantité doit être un nombre. ( Utilisé un '.' pour les décimaux )</strong>", true, 5000, 1000);
        giveLaserFocus();
    } else if (!okrange) {
        new MsgFactory("msg-box", "err", "<strong>La quantité doit être inférieur a 200 Unités</strong>", true, 5000, 1000);
        giveLaserFocus();
    } else if (okzeros) {
        new MsgFactory("msg-box", "err", "<strong>Une quantité de produit ne peux pas commencez par 0.</strong>", true, 5000, 1000);
        giveLaserFocus();
    }
}


socket.on("modify-product", function(context) {
    rmPlaceholder("done");
    if (context.original_state === "initial") {
        document.getElementById(context.uuid).remove();
        addPlaceholder("initial");
        new ProductFactory(context.product);
        new MsgFactory("msg-box", "ok", "<strong>Produit vérifié: </strong>"+context.product.name, true, 3000, 1000);

    } else if (context.original_state === "scanned") {
        rmFromScanned(context.uuid);
        let product = document.getElementById(context.uuid);
        if (product) {
            product.remove();
        }
        addPlaceholder("lmmodal");
        addPlaceholder("initial");
        new ProductFactory(context.product);
        new MsgFactory("msg-box", "ok", "<strong>Produit vérifié: </strong>"+context.product.name, true, 3000, 1000);

    } else {
        let product = document.getElementById(context.uuid);
        let span = product.getElementsByClassName("rcv")[0].getElementsByTagName("span")[0];
        product.className = "product border "+dstate(context.product);
        span.innerText = context.modifications.qty_received;
        new MsgFactory("msg-box", "ok", "<strong>Produit Modifié: </strong>"+context.product.name, true, 3000, 1000);
    }
});



socket.on("laser-scan", function(context) {
    console.log(context);
    new ProductFactory(context.product, false);
    waitingLaser("close");
});

socket.on("laser-scan-scanned", function(context) {
    waitingLaser("close")
    new MsgFactory("msg-box", "err", "<strong>Produit déjà scanné</strong>", true, 2000, 1000);
});
