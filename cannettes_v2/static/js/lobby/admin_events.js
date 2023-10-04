

// CLIENT EVENTS
////////////////////////////////////////////////////////////////////////////////////
document.getElementById('asmbl-btn').onclick = function() {
    let table = document.getElementById('room-verify-listing');
    let box = Array.from(table.getElementsByClassName('check'));
    let crit = mapAssemblySelectors(table, box);
    handleAssemblyErrors(crit[0], crit[1], crit[2], crit[3], crit[4]);
}


document.getElementById('del-btn').onclick = function() {
    let checked = getChecked();
    let index = checked[0];
    let ids = checked[1];

    if (index.length > 0) {
        for (var i = index.length - 1; i >= 0; i--) {
            room_list.deleteRow(index[i]);
            socket.emit('del_room', ids[i]);
        }
        check_empty_table('room-listing');

    } else {
        getErrorBox(
            'errorBox', 
            'errorText', 
            'solid 3px red', 
            `<strong>Vous devez selectionner un/des salons</strong>`,
            1500
        );
    }
}

document.getElementById('reset-btn').onclick = function() {
    let checked = getChecked();
    let index = checked[0];
    let ids = checked[1];

    if (index.length > 0) {
        for (const id of ids) {
            socket.emit('reset_room', id);
        }
        uncheckTheBox();

    } else {
        getErrorBox(
            'errorBox', 
            'errorText', 
            'solid 3px red', 
            `<strong>Vous devez selectionner un/des salons</strong>`,
            1500
        );
    }
}

qCodeBtn.addEventListener('click', () => {
    let domain = window.location.origin;
    let checked = getChecked();
    let index = checked[0];
    let ids = checked[1];

    if (index.length > 0) {
        socket.emit(
            'generate-qrcode-pdf', 
            {
                'origin': domain, 
                'room_ids': ids
            }
        );
        uncheckTheBox();
    } else {
        getErrorBox(
            'errorBox', 
            'errorText', 
            'solid 3px red', 
            `<strong>Vous devez selectionner un/des salons</strong>`, 
            1500
        );
    }
});

document.getElementById('create-btn').onclick = function() {
    const purContainer = document.getElementById('purchase-container');
    const invContainer = document.getElementById('inv-container');
    if (creationModal.style.display != 'flex') {
        window.scrollTo(0, window.scrollY); 
        document.getElementById('creation-modal').style.top = (window.scrollY - 5).toString() + 'px';
        creationModal.style.display = 'flex';
        purContainer.style.display = 'flex';
        invContainer.style.display = 'none';
        document.getElementById('html').style.overflowY = 'hidden';
    } else {
        creationModal.style.display = 'none';
        roomName.value = '';
        roomPassword.value = '';
        purchase.selectedIndex = 0;
        inventory.selectedIndex = 0;
    }
}


CancelCreationRoom.onclick = function() {
    creationModal.style.display = 'none';
    roomName.value = '';
    roomPassword.value = '';
    purchase.selectedIndex = 0;
    inventory.selectedIndex = 0;
    ptype.checked = false
    document.getElementById('html').style.overflowY = 'visible';
}

createRoom.onclick = function() {
    let type = getPType();
    let id = give_room_id();
    let attr = getObjectAttr(type);
    let name = roomName.value;
    let password = roomPassword.value;
    let object_id =  attr[0];
    let object_name = attr[1];

    if ((isNaN(object_id))) {
        // block empty pseudo purchase &  pseudo inventory
        HandleCreationErrors(
            'errorBox', 
            'errorText', 
            'solid 3px red', 
            `<strong>Il faut lier une commande au salon que vous créez</strong>`,
            1500
        );
    } else if (check_existence(object_name) && type == 'purchase') {
        HandleCreationErrors(
            'errorBox', 
            'errorText', 
            'solid 3px red', 
            `<strong>Cette commande est déjà liée à un salon</strong>`,
            1500
        );
    } else {
        let context = {
            'id': id, 
            'name': name, 
            'password':password,
            'object_type': type,
            'object_id': object_id
        };
        emitRoomCreation(context, type, name, id);
    }
}

socket.on('broadcast_room_assembler', (context) => {
    let table = document.getElementById('room-verify-listing');
    let box = Array.from(table.getElementsByClassName('check'));
    for (const [i, b] of box.entries()) {
        const id = table.rows[i + 1].cells[6].getElementsByClassName('join-btn').item(0).id;
        if (id == context.remove) {
            table.deleteRow(i + 1);
        }
        if (id == context.keep) {
            table.rows[i + 1].cells[1].innerHTML = ' assemblés';
        }
    }
}); 

// QRCODE 
socket.on('get-qrcode-pdf', (context) => {
    let buffer = context.pdf;
    let pdfWindow = window.open("");
    pdfWindow.document.write(
        "<iframe width='100%' height='100%' src='data:application/pdf;base64, " +
        encodeURI(buffer) + "'></iframe>"
    );
});