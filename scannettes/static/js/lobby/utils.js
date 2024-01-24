





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

    if (objectId === "categories") {
        selector.add(createOption("Aucun", ""), null);
    }
    
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
