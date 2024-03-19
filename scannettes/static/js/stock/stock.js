
keepLaserFocus();
rmProduct();
addPlaceholder("stock");

function keepLaserFocus() {
    let laser = document.getElementById("laser-output");
    laser.focus();
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
        if (okL && okChars) {
            laser.value = "";
            rmPlaceholder("stock");
            rmProduct();
            getProduct(barcode);
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

function rmProduct() {
    document.getElementById("stock-products").innerHTML = "";
}