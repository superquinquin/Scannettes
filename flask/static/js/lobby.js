
var browser = get_browser_id();
var suffix;
const currentLoc = window.location.href;
suffix = get_suffix(currentLoc);

const socket = io.connect(config.address);

// room main
const roomManagement = document.getElementById('room-management');
roomManagement.hidden = true;

const create_btn = document.getElementById('create-btn');
create_btn.disabled = true;

const del_btn = document.getElementById('del-btn');
del_btn.disabled = true;

const reset_btn = document.getElementById('reset-btn');
reset_btn.disabled = true;

const room_list = document.getElementById('room-listing');
const room_to_verify_list = document.getElementById('room-verify-listing');

const verifySection = document.getElementById('room-to-verify')
verifySection.hidden = true;
//modal
const roomName = document.getElementById('room-name');
const roomPassword = document.getElementById('room-password')
const purchase = document.getElementById('purchases');
const rayon = document.getElementById('rayons');
const creationModal = document.getElementById('creation-modal');
const createRoom = document.getElementById('createRoom');
const CancelCreationRoom = document.getElementById('CancelRoom');


/////// On connection [load existing, verify admin when suffix]
socket.on('connect', function() {
  console.log('has connected');

  socket.emit('message', 'Connection to lobby');
  socket.emit('join_lobby');
  if (suffix != 'lobby') {
    socket.emit('verify_connection', {'suffix': suffix, 'browser_id': browser})
  }
});

socket.on('load_existing_lobby', function(context) {

  empty_table('room-listing');
  empty_table('room-verify-listing');
  for (var row of context.room) {
    if (row[3] == 'open') {
      add_room_btn({'id': row[0], 'name': row[1], 'pur': row[2], 'status': row[3], 'creation_date': row[4], 'supplier': row[5]}, 'room-listing');
    } else {
      add_room_btn({'id': row[0], 'name': row[1], 'pur': row[2], 'status': row[3], 'creation_date': row[4], 'supplier': row[5]}, 'room-verify-listing');
    }
  }
  
  for (var option of context.selector) {
    add_purchase_selector({'id': option[0], 'name': option[1]})
  }
});  

socket.on('grant_permission', () => {
  console.log('grant permission')
  verifySection.hidden = false;
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
  for (var i = index.length - 1; i >= 0; i--) {
    room_list.deleteRow(index[i]);
    socket.emit('del_room', ids[i]);
  }

  check_empty_table('room-listing')
}

reset_btn.onclick = function() {
  let box = Array.from(document.getElementsByClassName('check'));
  for (const [i, b] of box.entries()) {
    if (b.checked) {
      const id = room_list.rows[i + 1].cells[6].getElementsByClassName('join-btn').item(0).id;
      socket.emit('reset_room', id);
    }
  }       
}

create_btn.onclick = function() {
  if (creationModal.style.display != 'flex') {
    creationModal.style.display = 'flex';
  } else {
    creationModal.style.display = 'none';
    roomName.value = '';
    roomPassword.value = '';
    purchase.selectedIndex = 0;
    rayon.selectedIndex = 0;
  }
}

/// MODAL BTN
CancelCreationRoom.onclick = function() {
  creationModal.style.display = 'none';
  roomName.value = '';
  roomPassword.value = '';
  purchase.selectedIndex = 0;
  rayon.selectedIndex = 0;
}

createRoom.onclick = function() {
  let name = roomName.value;
  let password = roomPassword.value;
  let pur = parseInt(purchase.options[purchase.selectedIndex].value);
  let ray = parseInt(rayon.options[rayon.selectedIndex].value);
  let id;
  id = give_room_id()

  socket.emit('create_room', {'name': name, 'password':password, 'pur': pur, 'ray': ray, 'id': id});
  creationModal.style.display = 'none';
  roomName.value = '';
  roomPassword.value = '';
  purchase.selectedIndex = 0;
  rayon.selectedIndex = 0;
}
   
socket.on('add_room', (context) => {
  add_room_btn(context, 'room-listing');
});      






// ROOM REDIRECTION

function redirect(id, index, tableID) {

  let table = document.getElementById(tableID)
  let password = table.rows[index].cells[5].getElementsByClassName('password').item(0).value;
  let winWidth = window.innerWidth 
  socket.emit('redirect', {'id': id, 'tableID': tableID, 'password': password, 'index': index, 'suffix': suffix, 'browser_id': browser, 'winWidth': winWidth});
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

function get_suffix(url) {
  let array = url.split('%26id%3D');
  if (array.length > 1) {
    suffix = '%26id%3D' + array[array.length - 1];
  } else {
    suffix = url.split('/')[url.split('/').length - 1];
  }
  return suffix;
}

function add_purchase_selector(input) {
  let id = input.id;
  let name = input.name;
  let option = document.createElement('option')
  option.value = id.toString();
  option.text = name.toString();
  purchase.add(option, null);
}

function give_room_id() {
  let openRooms = room_list.getElementsByTagName("button");
  let closeRooms = room_to_verify_list.getElementsByTagName("button");
  let activeRooms = openRooms.length + closeRooms.length
  let activeRoomsID = Array.from(openRooms).concat(Array.from(closeRooms)) 

  if (activeRooms == 0) {
    var id = 'room'+ activeRooms;
  } else {
    let ids = [];
    for (var i = 0, len = activeRooms ; i < len; i++) {
      let roomID = parseInt(activeRoomsID[i].id.slice(-1));
      ids.push(roomID);
    }
    ids.sort(function(a, b) {return a - b});

    var id = 'room'+ (ids[ids.length - 1] + 1).toString();
  }
  return id
}


// Table functions
function add_room_btn(input, tableID) {

  let table = document.getElementById(tableID)
  remove_empty_table_placeholder(tableID)

  let id = input.id;
  let status = input.status;
  let date = input.creation_date

  if (input.name == '') {
    var name = id;
  } else {
    var name = input.name;
  }

  if (typeof(input.pur) == 'number') {
    input.pur = "PO" + input.pur.toString()
  }

  if (input.pur == null || input.pur.slice(0,3) == 'spo') {
    var purchase = 'Aucune';
  } else {
    var supplier = input.supplier
    var purchase = input.pur + ' - ' + supplier;
  }


  let row = document.createElement('tr');

  let col0 = document.createElement('td');
  let checkBox = document.createElement('input')
  checkBox.setAttribute('type','checkbox')
  checkBox.setAttribute('class','check')
  col0.appendChild(checkBox);
  row.appendChild(col0);

  let col1 = document.createElement('td');
  col1.innerHTML = name;
  row.appendChild(col1);

  let col2 = document.createElement('td');
  if (typeof purchase == 'number') {
    col2.innerHTML = 'PO0'+purchase.toString()
  } else {
    col2.innerHTML = purchase;
  }
  row.appendChild(col2);

  let col3 = document.createElement('td');
  col3.innerHTML = status;
  row.appendChild(col3);

  let col4 = document.createElement('td');
  col4.innerHTML = date;
  row.appendChild(col4);

  let col5 = document.createElement('td');
  let inp = document.createElement("input");
  inp.setAttribute('class','password');
  inp.setAttribute('type','password');
  col5.appendChild(inp);
  row.appendChild(col5);

  let col6 = document.createElement('td');
  let btn = document.createElement("button");
  btn.setAttribute('id',id);
  btn.setAttribute('class', 'join-btn');
  btn.setAttribute('onclick',"redirect(this.id, get_parent_id(this, 2, 'i'), get_parent_id(this, 3, 'id'))");
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







