// CONTAINS ALL FUNCIONS FOR LOBBY

// FUNCTIONS
////////////////////////////////////////////////////////////////////////////////////

// ASSEMBLER
/////////////////////////////////////////////////////////////////////////////////////////
function mapAssemblySelectors(table, box) {
  let ids = [];
  let places = [];
  let names = [];
  let is_same_name = false;
  let is_diff_place = false;
  let active = false;
  let is_inv = true;

  for (const [i, b] of box.entries()) {
    if (b.checked) {
      b.checked = false;
      active = true;
      const id = table.rows[i + 1].cells[6].getElementsByClassName('join-btn').item(0).id;
      const type = table.rows[i + 1].cells[6].getElementsByClassName('join-btn').item(0).onclick.toString().match('inventory');
      const place = table.rows[i + 1].cells[1].innerHTML.match('stock|rayon');
      const name = table.rows[i + 1].cells[2].innerHTML;
      names.push(name)
      places.push(place);
      ids.push(id);
      if (!type) {
        is_inv = false;
      }
    }  
  }

  if (names.length == 2 && names[0] == names[1]) {
    is_same_name = true;
  }

  if (places.length == 2 &&
      places[0] && places[1] &&
      places[0].length == 1 &&
      places[1].length == 1 &&
      places[0][0] != places[1][0])
    is_diff_place = true;
  
  return [ids, active, is_inv, is_same_name, is_diff_place]
}

function handleAssemblyErrors(ids, active, is_inv, is_same_name, is_diff_place) {
  if (!active) {
    getErrorBox('errorBox', 
                'errorText', 
                'solid 3px red', 
                `<strong>Vous devez selectionner un/des salons !</strong>`,
                1500);
  } else if (!is_inv && ids.length != 2) {
    getErrorBox('errorBox', 
                'errorText', 
                'solid 3px red', 
                `<strong>Vous devez selectionner 2 inventaires. Les commandes ne sont pas acceptés !</strong>`,
                1500);
  } else if (!is_inv && ids.length == 2) {
    getErrorBox('errorBox', 
                'errorText', 
                'solid 3px red', 
                `<strong>Vous devez selectionner uniquement des inventaires !</strong>`,
                1500);
  } else if (is_inv && ids.length != 2) {
    getErrorBox('errorBox', 
                'errorText', 
                'solid 3px red', 
                `<strong>Vous devez selectionner 2 inventaires !</strong>`,
                1500); 
  
  } else if (!is_same_name) {
    getErrorBox('errorBox', 
                'errorText', 
                'solid 3px red', 
                `<strong>Les inventaires doivent être lié à la même catégorie de produits!</strong>`,
                1500); 
  
  } else if (!is_diff_place) {
    getErrorBox('errorBox', 
                'errorText', 
                'solid 3px red', 
                `<strong>Vous devez assembler un inventaire STOCK avec un inventaire RAYON!</strong>`,
                1500); 

  } else if (is_inv && ids.length == 2 && 
            is_same_name && is_diff_place) {
    // all good seding the ids to server
    socket.emit('room_assembler', {'ids': ids});
  }
}
/////////////////////////////////////////////////////////////////////////////////////////

// TABLES 
/////////////////////////////////////////////////////////////////////////
function check_empty_table(tableID) {
  // add placeholder if table is empty
  let table = document.getElementById(tableID);
  let box = Array.from(table.getElementsByClassName('check'));

  if (box.length == 0) {
    empty_table(tableID);
  }
}

function remove_empty_table_placeholder(tableID) {
  let table = document.getElementById(tableID)

  if (table.rows[1].cells[4].innerHTML === 'Aucun salon Ouvert') {
    table.deleteRow(1);
  }
}

function getChecked() {
  let index = [];
  let ids = [];
  let box = Array.from(room_list.getElementsByClassName('check'));
  for (const [i, b] of box.entries()) {
    if (b.checked) {
      const id = room_list.rows[i + 1].cells[6].getElementsByClassName('join-btn').item(0).id;
      index.push(i + 1);
      ids.push(id);
    }
  }
  return [index, ids]
}

function empty_table(tableID) {
  let table = document.getElementById(tableID);
  let row = document.createElement('tr');

  for (var i=0; i < 7; i++) {
    let col = document.createElement('td');
    if (i != 4) {
      col.innerHTML = '';
    } else {
      col.innerHTML = 'Aucun salon Ouvert';
    }
    row.appendChild(col);
  }
  table.appendChild(row);
}

function checkTheBox(rows, remove) {
  let allChecked = true;
  for (const row of rows) {
    let cell = row.getElementsByTagName('td');
    if (cell['0'] && cell['0'].innerHTML != "") {
      let check = cell['0'].children['0'].checked;

      if (remove == true) {
        cell['0'].children['0'].checked = false;

      } else if (!remove && !check) {
        allChecked = false;
        cell['0'].children['0'].checked = true;
      }
    }
  }
  return allChecked
}

function uncheckTheBox() {
  let box = Array.from(room_list.getElementsByClassName('check'));
  for (const [i, b] of box.entries()) {
    if (b.checked) {
      b.checked = false;
    }
  }
}
/////////////////////////////////////////////////////////////////////////


// UTILS
///////////////////////////////////////////////////////////////////////////////////

function add_selector(input, object) {
  const selector = document.getElementById(object);

  let id = input.id;
  let name = input.name;
  let option = document.createElement('option')
  option.value = id.toString();
  option.text = name.toString();
  selector.add(option, null);
}

function check_existence(purchase) {
  let check =  false;
  let open = document.getElementById('room-listing');
  let close = document.getElementById('room-verify-listing');
  let all_ar = Array.from(open.getElementsByClassName('check'))
                .concat(Array.from(close.getElementsByClassName('check')));
                
  for (const [i, b] of all_ar.entries()) {
    var existing_purchase = b.parentElement.parentElement.cells[2].innerHTML;
    if (purchase.split('-')[0] == existing_purchase.split('-')[0]) {
      check = true;
    }
  }
  return check
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

function translateStatus(status) {
  if (status == 'open') {
    status = 'ouvert';
  } else if (status == 'close') {
    status = 'fermé';
  } else {
    status = 'terminé'
  }
  return status
}

function europeanDate(date) {
  let seq = date.split(' ');
  let eH = seq[1].split(':').slice(0,2).join(':');

  let splD = seq[0].split('-');
  let eDate = [splD[2], splD[1], splD[0]].join('/');

  correctedDate = eDate + ' ' + eH;

  return correctedDate
}
///////////////////////////////////////////////////////////////////////////////////


// ROOM CREATION SUB FUNCTIONS
///////////////////////////////////////////////////////////////////////////////////
function getObjectAttr(type) {
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

function HandleCreationErrors(box, txt_container, bd_style, txt, time) {
  creationModal.style.display = 'none';
  roomName.value = '';
  roomPassword.value = '';
  purchase.selectedIndex = 0;
  inventory.selectedIndex = 0;
  ptype.checked = false

  getErrorBox(
    box, 
    txt_container, 
    bd_style, 
    txt,
    time
  );
}

function createDoubleInventory(context, name, id) {
  // rayon
  context.name = name + ' rayon';
  socket.emit('create_room', context);  

  // stock
  context.name = name + ' stock';
  context.id = 'room' + (parseInt(id.split('room')[1]) + 1).toString();
  socket.emit('create_room', context);
}

function emitRoomCreation(context, type, name, id) {
  if (type == 'inventory') {
    createDoubleInventory(context, name, id);
  } else {
    socket.emit('create_room', context);
  }

  document.getElementById('creation-info').innerHTML = "<strong>Création en cours...</strong>";
  createRoom.disabled = true;
  CancelCreationRoom.disabled = true;
}

function give_room_id() {
  let openRooms = room_list.getElementsByClassName("join-btn");
  let closeRooms = room_to_verify_list.getElementsByClassName("join-btn");
  let historicRoom = room_historic.getElementsByClassName("join-btn");
  let activeRooms = openRooms.length + closeRooms.length + historicRoom.length;
  let activeRoomsID = Array.from(openRooms).concat(Array.from(closeRooms));
  activeRoomsID = activeRoomsID.concat(Array.from(historicRoom));
  if (activeRooms == 0) {
    var id = 'room'+ activeRooms;

  } else {
    let ids = [];
    for (var i = 0, len = activeRooms ; i < len; i++) {
      let roomID = parseInt(activeRoomsID[i].id.split('room')[1]);
      ids.push(roomID);
    }
    ids.sort(function(a, b) {return a - b});
    var id = 'room'+ (ids[ids.length - 1] + 1).toString();
  }
  return id
}


// CREATE ROW
function add_room_btn(input, tableID) {
  let table = document.getElementById(tableID)
  remove_empty_table_placeholder(tableID)
  let row = document.createElement('tr');

  let col0 = document.createElement('td');
  let checkBox = document.createElement('input')
  checkBox.setAttribute('type','checkbox')
  checkBox.setAttribute('class','check')
  col0.appendChild(checkBox);
  row.appendChild(col0);

  let col1 = document.createElement('td');
  col1.innerHTML = input.name;
  row.appendChild(col1);

  let col2 = document.createElement('td');
  col2.innerHTML = input.object_name
  row.appendChild(col2);

  let col3 = document.createElement('td');
  col3.innerHTML = input.status;
  row.appendChild(col3);

  let col4 = document.createElement('td');
  if (input.status == 'done') {
    col4.innerHTML = europeanDate(input.date_closing);
  } else {
    col4.innerHTML = europeanDate(input.date_oppening);
  }
  row.appendChild(col4);

  let col5 = document.createElement('td');
  let inp = document.createElement("input");
  inp.setAttribute('class','password');
  inp.setAttribute('type','password');
  col5.appendChild(inp);
  row.appendChild(col5);

  let col6 = document.createElement('td');
  let btn = document.createElement("button");
  btn.setAttribute('id',input.id);
  btn.setAttribute('class', 'join-btn');
  if (input.object_type == 'purchase') {
    btn.setAttribute('onclick',"redirect_purchase(this)");
  } else {
    btn.setAttribute('onclick',"redirect_inventory(this)");
  }

  btn.appendChild(document.createTextNode('Rejoindre'));
  col6.appendChild(btn);
  row.appendChild(col6);

  table.appendChild(row);  
}
///////////////////////////////////////////////////////////////////////////////////

// JOINING ROOM REDIRECTION
//////////////////////////////////////////////////////////////////////////
function redirect(object, type) {
  let id = object.id;
  let index = get_parent(object, 2, 'i');
  let tableID = get_parent(object, 3, 'id');
  let password = get_parent(
    object, 
    2, 
    'object'
  ).cells[5].getElementsByClassName('password').item(0).value;
  let winWidth = window.innerWidth;

  socket.emit(
    'redirect', 
    {'id': id, 'tableID': tableID, 'password': password, 
    'index': index, 'type': type, 'suffix': suffix, 
    'browser_id': browser, 'winWidth': winWidth}
  );
}

function redirect_purchase(object) {
  let type = 'purchase';
  redirect(object, type);
}

function redirect_inventory(object, object) {
  let type = 'inventory';
  redirect(object, type);
}
//////////////////////////////////////////////////////////////////////

// ERROR CONTAINER 
////////////////////////////////////////////////////////////////////
function getErrorBox(box, txt_container, bd_style, txt, time) {
  let errorBox = document.getElementById(box);
  let errorText = document.getElementById(txt_container);
  errorBox.style.border = bd_style;
  errorText.innerHTML = txt;
  setTimeout(() => {
    errorBox.style.border = "0";
    errorText.innerHTML = "";
  }, time);
}
////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////