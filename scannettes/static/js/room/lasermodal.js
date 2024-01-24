
/////// LASER MODAL

function LMModal() {
    let modal = document.getElementById("lmmodal");
    let laser = document.getElementById("laser-output");
    if (modal.style.display === "block") {
        laser.value = "";
        modal.style.display = "none";
        lockwindow();
        document.getElementsByTagName("body")[0].removeEventListener("click", keepLaserFocus);
    } else {
        centerModal(modal);
        lockwindow();
        document.getElementsByTagName("body")[0].addEventListener("click", keepLaserFocus);
        laser.value = "";
        modal.style.display = "block"   
    }
}

function keepLaserFocus() {
    let modal = document.getElementById("lmmodal");
    let laser = document.getElementById("laser-output");
    if (
        modal.style.display === "block" 
        && laser != document.activeElement
        && !document.activeElement.className.match('mod-input')
        ) 
        {
            laser.focus();
        }
}

function RYaRdyYet(e) {
    let laser = document.getElementById("laser-output");
    if (e.key === "Enter" && document.activeElement === laser && laser.value.length > 0) {
        let barcode = laser.value;
        let okL = checkBarcodeLength(barcode);
        let okChars = checkIntChars(barcode);
        let okscan =  isNotScannedYet(barcode);
        let noscan = NoscannedProductyet();
        if (okL && okChars && okscan && noscan) {
            laser.value = "";
            waitingLaser("open");
            socket.emit("laser-scan", {"barcode": barcode, "rid": rid});
        } else if (!noscan) {
            laser.value = "";
            new MsgFactory("msg-box", "err", "<strong>Veuillez validé le produit déjà scanné.</strong>", true, 5000, 1000);
            // say that there already has a product scanned. no more than 1.
        } else if (!okscan) {
            laser.value = "";
            new MsgFactory("msg-box", "err", "<strong>Produit déja scanné</strong>", true, 5000, 1000);
            // say it is already scanned
        } else if (!okChars || !okL) {
            laser.value = "";
            new MsgFactory("msg-box", "err", "<strong>Une erreur s'est produite lors du scanning. Veuillez recommencer.</strong>", true, 5000, 1000);
            // say scanned did not work properly or the barcode is standart for the service
        }
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

function isNotScannedYet(barcode) {
    out = true;
    if (getScannedBarcodes().includes(barcode)) {
        out = false;
    }
    return out;
}

function NoscannedProductyet() {
    let out = false;
    const container = document.getElementById("scanned-products");
    let products = container.getElementsByClassName("product");
    console.log(products.length);
    if (products.length === 0) {
        out = true;
    }
    return out;
}

function getScannedBarcodes() {
    const container = document.getElementById("done");
    let products = container.getElementsByClassName("product");
    let scannedBarcodes = [];
    Array.from(products).forEach(function(p) {
        scannedBarcodes.push(p.getAttribute("barcodes"));
    });
    return scannedBarcodes;
}

function waitingLaser(action) {
    const loader = document.getElementById("laser-loader");
    if (action === "open") {
        rmPlaceholder("lmmodal");
        loader.style.display = "block";
    } else {
        addPlaceholder("lmmodal");
        loader.style.display = "none";
    }
}