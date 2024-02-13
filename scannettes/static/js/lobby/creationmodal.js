
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
    
    let display = modal.style.display;
    if (display != "block") {
        centerModal(modal);
        lockwindow();
        // modal.style.top = (window.scrollY - 5).toString() + 'px';
        // page.style.overflowY = 'hidden';
        modal.style.display = "block";
        WaitingCreation("close");
        switcher.checked = false;
        purContainer.style.display = 'block';
        invContainer.style.display = 'none';
        
    } else {
        modal.style.display = "none";
        WaitingCreation("close");
        roomName.value = '';
        roomPassword.value = '';
        purchase.selectedIndex = 0;
        inventory.selectedIndex = 0;
        switcher.checked = false;
        // page.style.overflowY = 'visible';
        lockwindow();
    }
}

function switchContainer() {
    const switcher = document.getElementById("pType-check");
    const purContainer = document.getElementById('purchase-container');
    const invContainer = document.getElementById('inv-container');
    if (switcher.checked) {
        purContainer.style.display = 'none';
        invContainer.style.display = 'block';
    } else {
        purContainer.style.display = 'block';
        invContainer.style.display = 'none';
    }
}



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

function WaitingCreation(action) {
    const loader = document.getElementById("loading-creation");
    const btns = document.getElementById("creation-btn");
    if (action === "open") {
        loader.style.display = "block";
        btns.style.display = "none";
    } else {
        btns.style.display = "block";
        loader.style.display = "none";
    }
}