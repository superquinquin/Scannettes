// CONTAINS ALL CLIENT AND SOCKET EVENTS FOR LOBBY 



// CLIENT EVENTS
////////////////////////////////////////////////////////////////////////////////////
document.getElementById('checkAll').onclick = function() {
  let table =  document.getElementById('room-listing');
  let rows = table.getElementsByTagName('tr');
  let allChecked = checkTheBox(rows, false);
  if (allChecked == true) {
    checkTheBox(rows, true);
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
////////////////////////////////////////////////////////////////////////////////////

// SOCKET EVENTS
////////////////////////////////////////////////////////////
socket.on('connect', function() {
  console.log('has connected');
  socket.emit('message', 'Connection to lobby');

  if (!charged && suffix != "lobby") {
    socket.emit('verify_connection', {'suffix': suffix, 'browser_id': browser});
  }

  if (!charged) {
    socket.emit('join_lobby');
    charged = true;
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

// ROOM CREATION
socket.on('add_room', (context) => {
  add_room_btn(context, 'room-listing');
  document.getElementById('html').style.overflowY = 'visible';
  document.getElementById('creation-info').innerHTML = "";
  creationModal.style.display = 'none';
  roomName.value = '';
  roomPassword.value = '';
  purchase.selectedIndex = 0;
  inventory.selectedIndex = 0;
  ptype.checked = false;
  createRoom.disabled = false;
  CancelCreationRoom.disabled = false;
});      

// ROOM REDIRECTION
socket.on('go_to_room', (data) => {
  window.location = data.url;
});

socket.on('access_denied', (context) => {
  let index = context.index;
  let table = document.getElementById(context.tableID);
  let field = table.rows[index].cells[5].getElementsByClassName('password').item(0);
  fadingRedFieldOnError(field);
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
  check_empty_table('room-listing');
});

socket.on('broacasted_finish', function(context) {
  let box = Array.from(room_list.getElementsByClassName('check'));

  for (const [i, b] of box.entries()) {
    const id = room_list.rows[i + 1].cells[6].getElementsByClassName('join-btn').item(0).id;
    if (id == context.roomID) {
      remove_empty_table_placeholder('room-verify-listing');
      room_to_verify_list.appendChild(room_list.rows[i + 1]);
    }
  }
  check_empty_table('room-listing');
});

///////////////////////////////////////////////////////////////////////////////////////////////////////
  