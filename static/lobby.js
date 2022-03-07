
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

//modal
const roomName = document.getElementById('room-name');
const roomPassword = document.getElementById('room-password')
const purchase = document.getElementById('purchases');
const rayon = document.getElementById('rayons')
const creationModal = document.getElementById('creation-modal');
const createRoom = document.getElementById('createRoom');
const CancelCreationRoom = document.getElementById('CancelRoom');



/////// On connection [load existing, verify admin when suffix]
socket.on('connect', function() {
  console.log('has connected');


  socket.emit('message', 'Connection to lobby');
  socket.emit('join_lobby');
  if (suffix != 'lobby') {
    socket.emit('verify_connection', suffix)
  }
});

socket.on('load_existing_lobby', function(context) {
  if (context.room.length === 0) {
    empty_table();
  } else {
    for (var row of context.room) {
      add_room_btn({'id': row[0], 'name': row[1], 'pur': row[2], 'status': row[3], 'creation_date': row[4]});
    }
  }
  for (var option of context.selector) {
    add_purchase_selector({'id': option[0], 'name': option[1]})
  }
});  

socket.on('grant_permission', () => {
  console.log('grant permission')
  roomManagement.hidden = false
  create_btn.disabled = false;
  del_btn.disabled = false;
  reset_btn.disabled = false;
});



/// MAIN BTN
del_btn.onclick = function() {
  let index = [];
  let ids = [];
  let box = Array.from(document.getElementsByClassName('check'));
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
  creationModal.style.display = 'flex';
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

  let activeRooms = room_list.getElementsByTagName("button").length;
  if (activeRooms == 0) {
    var id = 'room'+ activeRooms
  } else {
    let ids = []
    for (var i = 0, len = activeRooms ; i < len; i++) {
      let roomID = room_list.getElementsByTagName("button")[i].id
      ids.push(roomID)
    }

    var id = 'room'+ (parseInt(ids[ids.length - 1].slice(-1)) + 1).toString()
  }
  

  socket.emit('create_room', {'name': name, 'password':password, 'pur': pur, 'ray':ray, 'id': id});
  creationModal.style.display = 'none';
  roomName.value = '';
  roomPassword.value = '';
  purchase.selectedIndex = 0;
  rayon.selectedIndex = 0;
}
   
socket.on('add_room', (id) => {
  if (room_list.rows[1].cells[1].innerHTML === 'Aucune rooms Ouvertes') {
    console.log('del')
    room_list.deleteRow(1);
  }
  add_room_btn(id);
});      




// ROOM REDIRECTION

function redirect(id) {
  let row = Array.from(document.getElementsByClassName('join-btn'));
  let index;
  for (const [i, r] of row.entries()) {
    room_id = r.id;
    if (room_id == id) {
      index = i;
      password = room_list.rows[i + 1].cells[5].getElementsByClassName('password').item(0).value;
    }
  }
  socket.emit('redirect', {'id': id, 'password': password, 'index': index, 'suffix': suffix});
}

socket.on('go_to_room', (data) => {
  window.location = data.url;
});

socket.on('access_denied', (index) => {
  room_list.rows[index + 1].cells[5].getElementsByClassName('password').item(0).value = ''
  var color = 255;
  const colorFade = setInterval(() => {
    var c = color.toString();
    room_list.rows[index + 1].cells[5].getElementsByClassName('password').item(0).style.borderColor = 'rgb('+c+',0,0)';
    if (color == 150) {
      room_list.rows[index + 1].cells[5].getElementsByClassName('password').item(0).style.borderColor = 'black'
      clearInterval(colorFade);
    }
    color -= 5 ;
  }, 150);
});


// FUNCTIONS

function add_purchase_selector(input) {
  let id = input.id
  let name = input.name
  let option = document.createElement('option')
  option.value = id.toString();
  option.text = id.toString() + '-' + name.toString();
  purchase.add(option, null);
}



function add_room_btn(input) {
  let id = input.id;
  let status = input.status;
  let date = input.creation_date

  if (input.name == '') {
    var name = 'room'+id;
  } else {
    var name = input.name;
  }

  if (input.pur == '') {
    var purchase = 'Aucune';
  } else {
    var purchase = input.pur;
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
  col2.innerHTML = purchase;
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
  btn.setAttribute('onclick','redirect(this.id)');
  btn.appendChild(document.createTextNode('Rejoindre'));
  col6.appendChild(btn);
  row.appendChild(col6);

  room_list.appendChild(row);  
}


function empty_table() {
  let row = document.createElement('tr');

  let col1 = document.createElement('td');
  col1.innerHTML = '';
  row.appendChild(col1)

  let col2 = document.createElement('td');
  col2.innerHTML = 'Aucune rooms Ouvertes';
  row.appendChild(col2)

  let col3 = document.createElement('td');
  col3.innerHTML = '';
  row.appendChild(col3);

  let col5 = document.createElement('td');
  col5.innerHTML = '';
  row.appendChild(col5);

  let col6 = document.createElement('td');
  col6.innerHTML = '';
  row.appendChild(col6);

  room_list.appendChild(row);
}


function get_suffix(url) {
  let array = url.split('%26id%3D');
  if (array.length > 1) {
    suffix = array[array.length - 1];
  } else {
    suffix = url.split('/')[url.split('/').length - 1];
  }
  return suffix;
}