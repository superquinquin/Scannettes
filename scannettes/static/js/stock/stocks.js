
keepLaserFocus();
addPlaceholder("stock");

function keepLaserFocus() {
    if (!document.activeElement.classList.contains("searchbar")) {
        let laser = document.getElementById("laser-output");
        laser.focus();
    }
}

function getLaserOutput(e) {
    let laser = document.getElementById("laser-output");
    if (
        e.key != 'Shift' 
        && e.key != 'Enter' 
        && /^-?\d+$/.test(e.key)
        && document.activeElement === laser
        ) {
            laser.value += e.key;
    }
}

function RYaRdyYet(e) {
    let laser = document.getElementById("laser-output");
    if (e.key === "Enter" && document.activeElement === laser && laser.value.length > 0) {
        let barcode = laser.value;
        let okL = checkBarcodeLength(barcode);
        let okChars = checkIntChars(barcode);
        let okscan =  isNotScannedYet(barcode);
        if (okL && okChars && okscan) {
            laser.value = "";
            rmPlaceholder("stock");
            getProduct(barcode);
        } else if (!okscan) {
            laser.value = "";
            new MsgFactory("msg-box", "err", "<strong>Produit déja scanné</strong>", true, 5000, 1000);
        } else if (!okChars || !okL) {
            laser.value = "";
            new MsgFactory("msg-box", "err", "<strong>Une erreur s'est produite lors du scanning. Veuillez recommencer.</strong>", true, 5000, 1000);
            // say scanned did not work properly or the barcode is standart for the service
        } else {
            laser.value = "";
            new MsgFactory("msg-box", "err", "<strong>Une erreur s'est produite lors du scanning. Veuillez recommencer.</strong>", true, 5000, 1000);
        }
    }
}

function giveLaserFocus() {
    let laser = document.getElementById("laser-output");
    laser.focus();
}

function checkBarcodeLength(barcode) {
    let out = false;
    let curLength = barcode.length;
    if (curLength === 13 || curLength === 8) {
        out = true;
    }
    return out;
}

function checkIntChars(barcode) {
    out = false;
    let isnan = isNaN(Number(barcode));
    if (!isnan) {
        out=true;
    }
    return out;
}

function waitingLaser(action) {
    const loader = document.getElementById("laser-loader");
    if (action === "open") {
        loader.style.display = "block";
    } else {
        loader.style.display = "none";
    }
}

async function getProduct(barcode) {
    waitingLaser("open");
    payload = {
        method: "POST", 
        mode: "cors", 
        cache: "no-cache", 
        credentials: "same-origin", 
        headers: {"Content-Type": "application/json"}, 
        redirect: "follow", 
        referrerPolicy: "no-referrer",
        body: JSON.stringify({"barcode":barcode})
    };
    const response = await fetch("./getProduct", payload);
    const data = await response.json();
    waitingLaser("close");
    if (data.state == "err") {
        new MsgFactory("msg-box", "err", "<strong>"+data.message+"</strong>", true, 5000, 1000);
        addPlaceholder("stock");
    } else {
        new ProductFactory(data.product, false, true);
    }
}  




function isNotScannedYet(barcode) {
    out = true;
    if (getScannedBarcodes().includes(barcode)) {
        out = false;
    }
    return out;
}

function getScannedBarcodes() {
    const container = document.getElementById("stock");
    let products = container.getElementsByClassName("product");
    let scannedBarcodes = [];
    Array.from(products).forEach(function(p) {
        scannedBarcodes.push.apply(scannedBarcodes, p.getAttribute("barcodes").split(","));
    });
    return scannedBarcodes;
}

function delProducts() {
    const container = document.getElementById("stock-products");
    let nodes = container.getElementsByClassName("product");
    let selected = [];
    for (node of nodes) {
        let box = node.getElementsByClassName("pcheck")[0];
        if (box.checked) {
            selected.push(node);

        }
    }
    for (node of selected) {
        node.remove();
    }

    nodes = container.getElementsByClassName("product");
    if (nodes.length == 0) {
        addPlaceholder("stock");
    }
}

function rmProduct() {
    document.getElementById("stock-products").innerHTML = "";
    addPlaceholder("stock");
}