

var initialized = false;
const params = new URLSearchParams(window.location.search);
const rid = params.get("rid");
const admin = isAdmin();
var state;
var type;

const socket = io.connect(config.address);

socket.on("connect", function() {
    if (!initialized) {
        initialized = true;
        socket.emit('admin-initialization-call', {"instance": "room", "rid": parseInt(rid)});
    }
});

socket.on("room-initialization", function(context) {
    console.log(context);
    state = context.room.state;
    type = context.room.type;
    new MenuFactory(context.room);
    addProducts(context.data);
    addPlaceholder("initial");
    addPlaceholder("done");
});


// 

function isAdmin() {
    let admin = false;
    if (location.pathname.split('/')[1] === "admin") {
        admin = true
    }
    return admin;
}

//////////////////////////////  COLLAPSING BLOCKS

const collapser = document.getElementsByClassName("collaps-block");
for (var i = 0; i < collapser.length; i++) {
    collapser[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if (content.style.display == 'flex') {
            content.style.display = 'none';
        } else {
            content.style.display = 'flex';
        } 
    });
}


///////////////////////////// MENU BUILDER

class MenuFactory {
    constructor(payload) {
        this.infosContainer(payload);
        this.actionsContainer(payload);
    }

    infosContainer(payload) {
        let container = document.getElementById("info");
        container.appendChild(this.nameBuilder(payload.name, payload.rid));
        container.appendChild(this.typeBuilder(payload.type));
        container.appendChild(this.oidBuilder(payload.type, payload.oid));
        if (payload.type === "purchase") {
            container.appendChild(this.supplierBuilder(payload.supplier));
        }
        container.appendChild(this.dateBuilder(payload.creating_date));
        container.appendChild(this.stateBuilder(payload.state));
    }

    actionsContainer(payload) {
        let container = document.getElementById("actions");
        if (admin === false & payload.state === "open") {
            container.appendChild(this.btnBuilder("Terminer", "closeRoom()"));
        } else if (admin === true & payload.state === "open" & payload.type === "purchase") {
            container.appendChild(this.btnBuilder("Terminer", "closeRoom()"));
            container.appendChild(this.btnBuilder("Suspendre", "suspendRoom()"));
            container.appendChild(this.btnBuilder("Recharger", "rebaseRoom()"));
        } else if (admin === true & payload.state === "close" & payload.type === "purchase") {
            container.appendChild(this.btnBuilder("Valider", "validateRoom()"));
        } else if (admin === true & payload.state === "open" & payload.type === "inventory") {
            container.appendChild(this.btnBuilder("Terminer", "closeRoom()"));
            container.appendChild(this.btnBuilder("Suspendre", "suspendRoom()"));
        } else if (admin === true & payload.state === "close" & payload.type === "inventory") {
            container.appendChild(this.btnBuilder("Nullifier", "validateRoom()"));
            container.appendChild(this.btnBuilder("Valider", "validateRoom()"));
        }
    }

    btnBuilder(text, onclick) {
        let btn = document.createElement("button");
        btn.classList.add("mngmnt-btn", "stack");
        btn.innerText = text;
        btn.setAttribute("onclick", onclick);
        return btn;
    }

    infoBuilder(content) {
        let info = document.createElement("p");
        info.innerHTML = content;
        return info;
    }

    nameBuilder(name, rid) {
        let content = "<strong>Salon : </strong>";
        if (name === "") {
            name = "Salon n° " + rid;
        }
        content = content + name;
        return this.infoBuilder(content);
    }

    typeBuilder(type) {
        let content;
        if (type === "purchase") {
            content = "<strong>Type : </strong>Commande";
        } else if (type === "inventory") {
            content = "<strong>Type : </strong>Inventaire";
        }
        return this.infoBuilder(content);
    }

    oidBuilder(type, oid) {
        let content;
        if (type === "purchase") {
            content = "<strong>Commande : </strong>" + oid;
        } else if (type === "inventory") {
            content = "<strong>Inventaire : </strong>" + oid;
        }
        return this.infoBuilder(content);
    }

    supplierBuilder(fname) {
        let content = "<strong>Fournisseur : </strong>" + fname;
        return this.infoBuilder(content);
    }

    stateBuilder(state) {
        let content;
        if (state === "open") {
            content = "<strong>Statut : </strong> réception";
        } else if (state === "close") {
            content = "<strong>Statut : </strong> vérification";
        } else if (state === "done") {
            content = "<strong>Statut : </strong> archivé";
        }
        return this.infoBuilder(content);
    }

    dateBuilder(date) {
        let content = "<strong>Date : </strong>" + date;
        return this.infoBuilder(content);
    }
}

class ProductFactory {
    constructor(payload) {
        if (typeof payload === "string" || payload instanceof String) {
            let containerId = payload.split("-")[0];
            let container = document.getElementById(containerId);
            let placeholder = container.getElementsByClassName("placeholder-container")[0];
            placeholder.appendChild(this.placeHolder())
            return;
        }
        let container = document.getElementById(payload.state + "-products");
        let product = this.productBuilder(payload);

        product.appendChild(this.textCellBuilder(payload.name, "product-name"));
        product.appendChild(this.boxCellBuilder());
        product.appendChild(this.textCellBuilder(payload.barcodes, "product-barcode"));
        if (type === "purchase") {
            product.appendChild(this.textCellBuilder(
                "<strong>Unités:</strong> <span>"+payload.qty+"</span>",
                 "product-qty"
            ));
            product.appendChild(this.seperatorBuilder("sep1"));
            product.appendChild(this.textCellBuilder(
                "<strong>Paquets:</strong> <span>"+payload.qty_package+"</span>",
                "product-pkg"
            ));
            product.appendChild(this.seperatorBuilder("sep2"));
            product.appendChild(this.textCellBuilder(
                "<strong>Reçus:</strong> <span>"+payload.qty_received+"</span>",
                 "product-rcv"
            ));

        } else if (state === "inventaire") {
            product.appendChild(this.textCellBuilder(
                "<strong>Unités:</strong> <span>"+payload.qty_virtual+"</span>",
                 "product-qty"
            ));
            product.appendChild(this.textCellBuilder(
                "<strong>Reçus:</strong> <span>"+payload.qty_received+"</span>",
                 "product-rcv"
            ));
        }

        product.appendChild(this.textCellBuilder("<strong>Quantité Ok?</strong>", "product-ask"));
        product.appendChild(this.btnCellBuilder("Ok", "product-yes", "correctProductQty(this)"));
        product.appendChild(this.btnCellBuilder("Modifier", "product-mod", "modifyProductQty(this)"));
        
        this.visibility(product, payload);
        container.appendChild(product);
    }

    productBuilder(payload) {
        let product = document.createElement("div");
        let nonAttr = ["name", "barcode", "qty", "qty_package", "qty_preceived", "qty_virtual"];
        for (var key in payload) {
            if (!nonAttr.includes(key)) {
                product.setAttribute(key, payload[key]);
            }
        }
        product.setAttribute("id", payload.uuid);
        product.classList.add("product", this._dstate(payload));
        return product;
    }

    textCellBuilder(text, cls) {
        let cell = document.createElement("div");
        cell.classList.add("grid-cell", cls);
        cell.innerHTML = text;
        return cell;
    }

    boxCellBuilder() {
        let cell = document.createElement("div");
        cell.classList.add("grid-cell", "product-check");

        let inp = document.createElement("input");
        inp.setAttribute("type", "checkbox");
        inp.classList.add("pcheck");

        cell.appendChild(inp);
        return cell;
    }

    seperatorBuilder(cls) {
        let cell = document.createElement("div");
        cell.classList.add("grid-cell", cls);

        let sep = document.createElement("div");
        sep.classList.add("separator");

        cell.appendChild(sep);
        return cell;
    }

    btnCellBuilder(text, cls, onclick) {
        let cell = document.createElement("div");
        cell.classList.add("grid-cell", cls);

        let btn = document.createElement("button");
        btn.setAttribute("onclick", onclick);
        btn.classList.add("mngmnt-btn");
        btn.innerText = text;

        cell.appendChild(btn);
        return cell;
    }

    visibility(product, payload) {
        // from room status
        if (state === "done") {
            product.getElementsByClassName("product-ask")[0].style.display = "none";
            product.getElementsByClassName("product-yes")[0].style.display = "none";
            product.getElementsByClassName("product-mod")[0].style.display = "none";
            return product;
        }

        // from item state
        if (payload.state === "open" & state === "purchase") {
            product.getElementsByClassName("sep2")[0].style.display = "none";
            product.getElementsByClassName("product-rcv")[0].style.display = "none";
        } else if (payload.state === "open" & state === "inventory") {
            product.getElementsByClassName("product-rcv")[0].style.display = "none";
        } else if (payload.state === "done") {
            product.getElementsByClassName("product-yes")[0].style.display = "none";
        }

        // admin and uomid is not units (can be enlarged).
        if (!admin & [1].includes(payload.uomid)) {
            product.getElementsByClassName("product-ask")[0].style.display = "none";
            product.getElementsByClassName("product-yes")[0].style.display = "none";
            product.getElementsByClassName("product-mod")[0].style.display = "none";
        }
        return product;
    }

    _dstate(payload) {
        let cls = {0: "normal", 1: "new", 2: "modified", 3: "unknown"};
        let values = {"_new": 1, "_modified": 2, "_unknown": 3}
        let maxx = 0;
        for (var key in payload) {
            if (
                Object.keys(values).includes(key) 
                & payload[key]
                & values[key] > maxx
                ) 
                {
                    maxx = values[key];
            } 
        }
        return cls[maxx];
    }

    placeHolder() {
        let elm = document.createElement("div");
        elm.classList.add("placeholder");

        let text = document.createElement("p");
        text.innerText = "Aucun produit";

        elm.appendChild(text);
        return elm;
    }
}


function addProducts(products) {
    for (product of products) {
        new ProductFactory(product);
    }
}

function rmPlaceholder(containerId) {
    const container = document.getElementById(containerId);
    let placeholder = container.getElementsByClassName("placeholder");
    if (placeholder.length > 0) {
        placeholder[0].remove();
    }
}

function addPlaceholder(containerId) {
    const container = document.getElementById(containerId);
    let purchases = container.getElementsByClassName("product");
    let placeholder = container.getElementsByClassName("placeholder");
    if (purchases.length === 0 & placeholder.length === 0) {
        new ProductFactory(containerId+"-placeholder");
    }
}