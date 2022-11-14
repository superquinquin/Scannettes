
var browser = get_browser_id();
var suffix;
var charged = false;
const currentLoc = window.location.href;
suffix = get_suffix(currentLoc);

const socket = io.connect(config.ADDRESS);

// room main
const roomManagement = document.getElementById('room-management');
roomManagement.hidden = true;

const create_btn = document.getElementById('create-btn');
create_btn.disabled = true;

const del_btn = document.getElementById('del-btn');
del_btn.disabled = true;

const reset_btn = document.getElementById('reset-btn');
reset_btn.disabled = true;

const asmbl_btn = document.getElementById('asmbl-btn');
asmbl_btn.disabled = true;

const room_list = document.getElementById('room-listing');
const room_to_verify_list = document.getElementById('room-verify-listing');
const room_historic = document.getElementById('room-historic');

const verifySection = document.getElementById('room-to-verify');
verifySection.hidden = true;

const historicSection = document.getElementById('historic');
historicSection.hidden = true;
//modal
const roomName = document.getElementById('room-name');
const roomPassword = document.getElementById('room-password');
const purchase = document.getElementById('purchases');
const inventory = document.getElementById('rayons');
const creationModal = document.getElementById('creation-modal');
const ptype = document.getElementById('pType-check');
const createRoom = document.getElementById('createRoom');
const CancelCreationRoom = document.getElementById('CancelRoom');


/////// On connection [load existing, verify admin when suffix]
socket.on('connect', function() {
  console.log('has connected');

  socket.emit('message', 'Connection to lobby');
  if (charged == false) {
    socket.emit('join_lobby');
    charged = true;

    if (suffix != 'lobby') {
      socket.emit('verify_connection', {'suffix': suffix, 'browser_id': browser})
    }
  }
});

socket.on('load_existing_lobby', function(context) {

  empty_table('room-listing');
  empty_table('room-verify-listing');
  empty_table('room-historic');
  for (var row of context.room) {
    if (row.status == 'open') {
      add_room_btn(row, 'room-listing');
    } else if (row.status == 'close') {
      add_room_btn(row, 'room-verify-listing');
    } else {
      add_room_btn(row, 'room-historic');
    }
  }
  
  for (var option of context.selector) {
    add_selector({'id': option[0], 
                  'name': option[1]}, 
                  'purchases')
  }

  for (var option of context.selector_inv) {
    add_selector({'id': option[1], 
                  'name': option[0]}, 
                  'rayons')
  }

});  

socket.on('grant_permission', () => {
  console.log('grant permission')
  verifySection.hidden = false;
  historicSection.hidden = false;
  roomManagement.hidden = false;
  create_btn.disabled = false;
  del_btn.disabled = false;
  reset_btn.disabled = false;

});



/// MAIN BTN
del_btn.onclick = function() {
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

  if (index.length > 0) {
    for (var i = index.length - 1; i >= 0; i--) {
      room_list.deleteRow(index[i]);
      socket.emit('del_room', ids[i]);
    }
    check_empty_table('room-listing')

  } else {
    getErrorBox('errorBox', 
                'errorText', 
                'solid 3px red', 
                `<strong>Vous devez selectionner un/des salons</strong>`,
                1500);
  }
}

reset_btn.onclick = function() {
  let table = document.getElementById('room-listing');
  let box = Array.from(table.getElementsByClassName('check'));
  let active = false;
  for (const [i, b] of box.entries()) {
    if (b.checked) {
      b.checked = false;
      active = true;
      const id = table.rows[i + 1].cells[6].getElementsByClassName('join-btn').item(0).id;
      socket.emit('reset_room', id);
    }
  }
  
  if (active == false) {
    getErrorBox('errorBox', 
                'errorText', 
                'solid 3px red', 
                `<strong>Vous devez selectionner un/des salons</strong>`,
                1500);
  }
}

const checkAll = document.getElementById('checkAll');
checkAll.onclick = function() {
  let table =  document.getElementById('room-listing');
  let rows = table.getElementsByTagName('tr');
  let allChecked = checkTheBox(rows, false);
  if (allChecked == true) {
    checkTheBox(rows, true);
  }
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


create_btn.onclick = function() {
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

ptype.onclick = function() {
  const purContainer = document.getElementById('purchase-container');
  const invContainer = document.getElementById('inv-container');
  if (ptype.checked) {
    purContainer.style.display = 'none';
    invContainer.style.display = 'flex';
  } else {
    purContainer.style.display = 'flex';
    invContainer.style.display = 'none';
  }
}


/// MODAL BTN
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
  // let pur = parseInt(purchase.options[purchase.selectedIndex].value);
  // let purchase_name = purchase.options[purchase.selectedIndex].innerHTML;
  // let inventory_cat_id = parseInt(inventory.options[inventory.selectedIndex].value);
  // let inventory_cat_name = inventory.options[inventory.selectedIndex].innerHTML;

  let type = getPType();
  let id = give_room_id();
  let name = roomName.value;
  let password = roomPassword.value;
  let object_id;
  let object_name;
  if (type == 'purchase') {
    object_id = parseInt(purchase.options[purchase.selectedIndex].value);
    object_name = purchase.options[purchase.selectedIndex].innerHTML;
  } else {
    object_id = parseInt(inventory.options[inventory.selectedIndex].value);
    object_name = inventory.options[inventory.selectedIndex].innerHTML;
  }
  document.getElementById('html').style.overflowY = 'visible';


  if ((isNaN(object_id))) {
    // block empty pseudo purchase &  pseudo inventory
    creationModal.style.display = 'none';
    roomName.value = '';
    roomPassword.value = '';
    purchase.selectedIndex = 0;
    inventory.selectedIndex = 0;
    ptype.checked = false

    getErrorBox('errorBox', 
                'errorText', 
                'solid 3px red', 
                `<strong>Il faut lier une commande au salon que vous créez</strong>`,
                1500);

 
  } else if (check_existence(object_name) && type == 'purchase') {
    creationModal.style.display = 'none';
    roomName.value = '';
    roomPassword.value = '';
    purchase.selectedIndex = 0;
    inventory.selectedIndex = 0;
    ptype.checked = false

    getErrorBox('errorBox', 
                'errorText', 
                'solid 3px red', 
                `<strong>Cette commande est déjà liée à un salon</strong>`,
                1500);

  } else {
    socket.emit('create_room', {'id': id, 
                                'name': name, 
                                'password':password,
                                'object_type': type,
                                'object_id': object_id});
    document.getElementById('creation-info').innerHTML = "<strong>Création en cours...</strong>";
    createRoom.disabled = true;
    CancelCreationRoom.disabled = true;
  }
}
   
socket.on('add_room', (context) => {
  add_room_btn(context, 'room-listing');
  creationModal.style.display = 'none';
  roomName.value = '';
  roomPassword.value = '';
  purchase.selectedIndex = 0;
  inventory.selectedIndex = 0;
  ptype.checked = false;
  document.getElementById('creation-info').innerHTML = "";
  createRoom.disabled = false;
  CancelCreationRoom.disabled = false;
});      



function getPType() {
  let check =  document.getElementById('pType-check').checked;
  if (check) {
    var pType = 'inventory';
  } else {
    var pType = 'purchase';
  }
  return pType
}



// ROOM REDIRECTION

function redirect_purchase(object) {
  let type = 'purchase';
  let id = object.id;
  let tableID = get_parent(object, 3, 'id');
  let password = get_parent(object, 
                            2, 
                            'object').cells[5].getElementsByClassName('password').item(0).value;
  let index = get_parent(object, 2, 'i');
  let winWidth = window.innerWidth;

  socket.emit('redirect', 
              {'id': id, 'tableID': tableID, 'password': password, 
              'index': index, 'type': type, 'suffix': suffix, 
              'browser_id': browser, 'winWidth': winWidth});
}

function redirect_inventory(object) {
  let type = 'inventory';
  let id = object.id;
  let tableID = get_parent(object, 3, 'id');
  let password = get_parent(object, 
                            2, 
                            'object').cells[5].getElementsByClassName('password').item(0).value;
  let index = get_parent(object, 2, 'i');
  let winWidth = window.innerWidth;

  socket.emit('redirect', 
              {'id': id, 'tableID': tableID, 'password': password, 
              'index': index, 'type': type, 'suffix': suffix, 
              'browser_id': browser, 'winWidth': winWidth});
}

socket.on('go_to_room', (data) => {
  window.location = data.url;
});

socket.on('access_denied', (context) => {
  let index = context.index;
  let table = document.getElementById(context.tableID);
  table.rows[index].cells[5].getElementsByClassName('password').item(0).value = '';

  var color = 255;
  const colorFade = setInterval(() => {
    var c = color.toString();
    table.rows[index].cells[5].getElementsByClassName('password').item(0).style.borderColor = 'rgb('+c+',0,0)';
    if (color == 150) {
      table.rows[index].cells[5].getElementsByClassName('password').item(0).style.borderColor = 'black';
      clearInterval(colorFade);
    }
    color -= 5;
  }, 150);
});


// CLOSING ROOM CALL

socket.on('broacasted_suspension', function(context) {
  let box = Array.from(room_list.getElementsByClassName('check'));

  for (const [i, b] of box.entries()) {
    const id = room_list.rows[i + 1].cells[6].getElementsByClassName('join-btn').item(0).id;
    if (id == context.roomID) {
      room_list.deleteRow(i + 1);
    }
  }
  check_empty_table('room-listing')
});


socket.on('broacasted_finish', function(context) {
  let box = Array.from(room_list.getElementsByClassName('check'));

  for (const [i, b] of box.entries()) {
    const id = room_list.rows[i + 1].cells[6].getElementsByClassName('join-btn').item(0).id;
    if (id == context.roomID) {
      remove_empty_table_placeholder('room-verify-listing')
      room_to_verify_list.appendChild(room_list.rows[i + 1])
    }
  }
  check_empty_table('room-listing')
});


// FUNCTIONS

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

function get_suffix(url) {
  let array = url.split('%26id%3D');
  if (array.length > 1) {
    suffix = '%26id%3D' + array[array.length - 1];
  } else {
    suffix = url.split('/')[url.split('/').length - 1];
  }
  return suffix;
}

function add_selector(input, object) {
  const selector = document.getElementById(object);

  let id = input.id;
  let name = input.name;
  let option = document.createElement('option')
  option.value = id.toString();
  option.text = name.toString();
  selector.add(option, null);
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

function europeanDate(date) {
  let seq = date.split(' ');
  let eH = seq[1].split(':').slice(0,2).join(':');

  let splD = seq[0].split('-');
  let eDate = [splD[2], splD[1], splD[0]].join('/');

  correctedDate = eDate + ' ' + eH;

  return correctedDate
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


// Table functions
function add_room_btn(input, tableID) {
  console.log(input.object_type)
  let table = document.getElementById(tableID)
  remove_empty_table_placeholder(tableID)
  console.log(input.date_oppening)
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
    console.log('pur')
    btn.setAttribute('onclick',"redirect_purchase(this)");
  } else {
    console.log('inv')
    btn.setAttribute('onclick',"redirect_inventory(this)");
  }

  btn.appendChild(document.createTextNode('Rejoindre'));
  col6.appendChild(btn);
  row.appendChild(col6);

  table.appendChild(row);  
}


function empty_table(tableID) {
  let table = document.getElementById(tableID)
  let row = document.createElement('tr');

  for (var i=0; i < 7; i++) {
    let col = document.createElement('td');
    if (i != 4) {
      col.innerHTML = '';
    } else {
      col.innerHTML = 'Aucun salon Ouvert';
    }
    row.appendChild(col)
  }
  table.appendChild(row);
}



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



//// QRCODE /////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////

const qCodeBtn = document.getElementById('qrcode-btn');

qCodeBtn.addEventListener('click', () => {
  let table = document.getElementById('room-listing');
  let domain = window.location.origin;
  let ArID = [];

  if (table.rows[1].cells[4].innerHTML === 'Aucun salon Ouvert') {
    getErrorBox('errorBox', 
                'errorText', 
                'solid 3px red', 
                `<strong>Vous devez selectionner un/des salons</strong>`, 
                1500)

  } else {

    let box = Array.from(table.getElementsByClassName('check'));
    for (const [i, b] of box.entries()) {
      if (b.checked) {
        b.checked = false;
        const id = table.rows[i + 1].cells[6].getElementsByClassName('join-btn').item(0).id;
        ArID.push(id);
      }
    }
    if (ArID.length > 0) {
      socket.emit('generate-qrcode-pdf', {'origin': domain, 
                  'room_ids': ArID});
    } else {
      getErrorBox('errorBox', 
                  'errorText', 
                  'solid 3px red', 
                  `<strong>Vous devez selectionner un/des salons</strong>`, 
                  1500)
    }
  }
});


socket.on('get-qrcode-pdf', (context) => {
  let buffer = context.pdf;
  let pdfWindow = window.open("");
  pdfWindow.document.write(
      "<iframe width='100%' height='100%' src='data:application/pdf;base64, " +
      encodeURI(buffer) + "'></iframe>"
  );
});









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


