
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


class ProductFactory {
    constructor(payload, wId=true) {
        if (typeof payload === "string" || payload instanceof String) {
            let containerId = payload.split("-")[0];
            let container = document.getElementById(containerId);
            let placeholder = container.getElementsByClassName("placeholder-container")[0];
            placeholder.appendChild(this.placeHolder())
            return;
        }

        let container = document.getElementById(payload.state + "-products");
        let product = this.productBuilder(payload, wId);
        product = this.infoBlock(product, payload);
        product = this.qtyBlock(product, payload);
        product = this.askBlock(product, payload);
        product = this.inputBlock(product, payload);
        container.appendChild(product);
        // this.visibility(product, payload);
    }

    infoBlock(frame, payload) {
        frame.appendChild(this.textCellBuilder(payload.name, ["product-name"]));
        frame.appendChild(this.boxCellBuilder());
        frame.appendChild(this.textCellBuilder(payload.barcodes, ["product-barcode"]));
        return frame;
    }

    qtyBlock(frame, payload) {
        let uom = {1: "Unités", 3: "Kilos", "11": "Litres", "21": "Kilos"};
        let units_name = uom[payload.uomid] || "Unités";
        
        round(payload.qty_virtual);

        if (type === "purchase") {
            frame.appendChild(this.textCellBuilder(
                "<strong>Colis:</strong> <span>"+round(payload.qty_package)+"</span>",
                ["product-pkg"]
            ));
            frame.appendChild(this.seperatorBuilder("sep1"));
            frame.appendChild(this.textCellBuilder(
                "<strong>"+units_name+":</strong> <span>"+round(payload.qty)+"</span>",
                ["product-qty"]
            ));

            if (payload.state === "done") { 
                frame.appendChild(this.seperatorBuilder("sep2"));
                frame.appendChild(this.textCellBuilder(
                    "<strong>Reçues:</strong> <span>"+payload.qty_received+"</span>",
                    ["product-rcv", "rcv"]
                ));
            }

        } else if (type === "inventory") {
            frame.appendChild(this.textCellBuilder(
                "<strong>Stock ("+units_name+"):</strong> <span>"+round(payload.qty_virtual)+"</span>",
                ["stock"]
            ));

            if (payload.state === "done") {
                frame.appendChild(this.textCellBuilder(
                    "<strong>Stock réel:</strong> <span>"+payload.qty_received+"</span>",
                    ["stock-real", "rcv"]
                ));
            }
        }
        return frame;
    }

    askBlock(frame, payload) {
        if (admin && state === "done") {
            return frame;

        } else if (admin && payload.state != "done") {
            frame.appendChild(this.textCellBuilder("<strong>Quantité Ok?</strong>", ["product-ask"]));
            frame.appendChild(this.btnCellBuilder("Ok", ["product-yes"], "correctProductQty(this)"));
            frame.appendChild(this.btnCellBuilder("Modifier", ["product-mod"], "OpenModification(this)"));

        } else if (admin && payload.state === "done") {
            frame.appendChild(this.textCellBuilder("<strong>Quantité Ok?</strong>", ["product-ask"]));
            frame.appendChild(this.btnCellBuilder("Modifier", ["product-mod"], "OpenModification(this)"));

        } else if (!admin && payload.state === "initial" && payload.uomid == 1) {
            return frame;

        } else if ((!admin && payload.state === "scanned" ) || (!admin && payload.state === "initial" && payload.uomid != 1)) {
            frame.appendChild(this.textCellBuilder("<strong>Quantité Ok?</strong>", ["product-ask"]));
            frame.appendChild(this.btnCellBuilder("Ok", ["product-yes"], "correctProductQty(this)"));
            frame.appendChild(this.btnCellBuilder("Modifier", ["product-mod"], "OpenModification(this)"));

        } else if (!admin && payload.state === "done") {
            frame.appendChild(this.textCellBuilder("<strong>Quantité Ok?</strong>", ["product-ask"]));
            frame.appendChild(this.btnCellBuilder("Modifier", ["product-mod"], "OpenModification(this)"));
        }
        return frame;
    }

    inputBlock(frame, payload) {
        if (!admin && payload.state === "initial" && payload.uomid == 1) {
            return frame;
        } else {
            frame.appendChild(this.inputCellBuilder());
            frame.appendChild(this.btnCellBuilder("Confirmer", ["apply-mod"], "modifyProductQty(this)"));
            frame.getElementsByClassName("product-mod-input")[0].style.display = "none";
            frame.getElementsByClassName("apply-mod")[0].style.display = "none";
        }
        return frame;
    }

    productBuilder(payload, wId) {
        let product = document.createElement("div");
        let nonAttr = ["qty", "qty_package", "qty_preceived", "qty_virtual"];
        for (var key in payload) {
            if (!nonAttr.includes(key)) {
                product.setAttribute(key, payload[key]);
            }
        }
        if (wId) {
            product.setAttribute("id", payload.uuid);
        }
        product.classList.add("product", "border", this._dstate(payload));
        return product;
    }

    textCellBuilder(text, cls) {
        let cell = document.createElement("div");
        cell.classList.add("grid-cell", ...cls);
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
        btn.classList.add("btn-small", "border");
        btn.innerText = text;

        cell.appendChild(btn);
        return cell;
    }

    inputCellBuilder() {
        let inp = document.createElement("input");
        inp.setAttribute("type", "text");
        inp.setAttribute("inputmode", "numeric");
        inp.setAttribute("maxlength", "3");
        inp.setAttribute("placeholder", "Quantité reçue...");
        inp.setAttribute("onkeypress", "keyModify(event, this)");
        inp.classList.add("grid-cell", "product-mod-input", "border", "sfield-text-inp");
        return inp;
    }

    _dstate(payload) {
        return dstate(payload);
    }

    placeHolder() {
        let elm = document.createElement("div");
        elm.classList.add("placeholder", "border");

        let text = document.createElement("p");
        text.innerText = "Aucun produit";

        elm.appendChild(text);
        return elm;
    }
}

function isInt(n) {
    return n % 1 === 0;
}


function round(val) {
    if (val == 0) {
        return val;
    } else if (typeof val === "number" && isInt(val)) {
        if (val > 999) {
            return "999+";
        } else {
            return val;
        }
    } else if (typeof val === "number" && !isInt(val)) {
        let spl = val.toString().split('.');
        return spl[0]+"."+spl[1][0];
    }
}


function dstate(payload) {
    let cls = {0: "normal", 1: "new", 2: "modified", 3: "unknown"};
    let purValues = {"_modified": 1, "_new": 2, "_unknown": 3}
    let invValues = {"sdiff": 10, "mdiff": 20, "ldiff": 30, "xldiff": 40} 
    if (type === "purchase") {
        let maxx = 0;
        for (var key in payload) {
            if (
                Object.keys(purValues).includes(key) 
                & payload[key]
                & purValues[key] > maxx
                ) 
                {
                    maxx = purValues[key];
            } 
        }
        return cls[maxx];

    } else if (type === "inventory" && payload.state != "done") {
        return "normal";

    } else if (type === "inventory" && payload.state === "done") {
        let minn = "normal";
        Object.keys(invValues).forEach(function(key) {
            let diff = Math.abs(payload.qty_received - payload.qty_virtual);
            if (diff >= invValues[key]) {
                minn = key;
            }
        });
        return minn;
    }
}