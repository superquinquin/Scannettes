var config = {"ADDRESS": "http://localhost:5000", "COLOR_PRIMARY": "#fefa85", "COLOR_SECONDARY": "#3C312E", "COLOR_TERNARY": "#FAEFEF", "COLOR_NEW_ITEMS": "#FD8789", "COLOR_NEW_ITEMS_IF_EXIST": "#B5B3D0", "COLOR_MOD_ITEMS": "#FDC087", "COLOR_NORMAL_ITEMS": "#CFF2E8", "CAMERA_ENABLE_VIDEO": true, "CAMERA_ENABLE_AUDIO": false, "CAMERA_IDEAL_WIDTH": 1920, "CAMERA_IDEAL_HEIGHT": 1080, "CAMERA_IDEAL_MODE": "environment", "CAMERA_FRAME_WIDTH": 300, "CAMERA_FRAME_HEIGHT": 200, "CAMERA_FPS": 120, "CAMERA_PKG_FREQUENCY": 2};
// INIT SOCKET AND VARIABLE FOR LOBBY.

const currentLoc = window.location.href;
var suffix = get_suffix(currentLoc);
var browser = get_browser_id();
var charged = false;

const socket = io.connect(config.ADDRESS);
//MAIN
const root = document.documentElement;
const roomManagement = document.getElementById('room-management');
const roomAssembler = document.getElementById('room-assembler');
const create_btn = document.getElementById('create-btn');
const del_btn = document.getElementById('del-btn');
const reset_btn = document.getElementById('reset-btn');
const asmbl_btn = document.getElementById('asmbl-btn');
const room_list = document.getElementById('room-listing');
const room_to_verify_list = document.getElementById('room-verify-listing');
const room_historic = document.getElementById('room-historic');
const verifySection = document.getElementById('room-to-verify');
const historicSection = document.getElementById('historic');
const checkAll = document.getElementById('checkAll');
//Modal
const roomName = document.getElementById('room-name');
const roomPassword = document.getElementById('room-password');
const purchase = document.getElementById('purchases');
const inventory = document.getElementById('rayons');
const creationModal = document.getElementById('creation-modal');
const ptype = document.getElementById('pType-check');
const createRoom = document.getElementById('createRoom');
const CancelCreationRoom = document.getElementById('CancelRoom');
//QRCODE
const qCodeBtn = document.getElementById('qrcode-btn');

historicSection.hidden = true;
verifySection.hidden = true;
asmbl_btn.disabled = true;
reset_btn.disabled = true;
del_btn.disabled = true;
create_btn.disabled = true;
roomManagement.hidden = true;
roomAssembler.hidden = true;


// INIT FUNCTION
root.style.setProperty('--primary', config.COLOR_PRIMARY);
root.style.setProperty('--secondary', config.COLOR_SECONDARY);
root.style.setProperty('--ternary', config.COLOR_TERNARY);

function get_suffix(url) {
    let array = url.split('%26id%3D');
    if (array.length > 1) {
      suffix = '%26id%3D' + array[array.length - 1];
    } else {
      suffix = url.split('/')[url.split('/').length - 1];
    }
    return suffix;
  }


function get_browser_id() {
  var browser;
  let ua = navigator.userAgent.toLowerCase();
  let Sys = {};
  let s;
  (s = ua.match(/msie ([\d.]+)/)) ? Sys.ie = s[1] :
  (s = ua.match(/firefox\/([\d.]+)/)) ? Sys.firefox = s[1] :
  (s = ua.match(/chrome\/([\d.]+)/)) ? Sys.chrome = s[1] :
  (s = ua.match(/opera.([\d.]+)/)) ? Sys.opera = s[1] :
  (s = ua.match(/version\/([\d.]+).*safari/)) ? Sys.safari = s[1] : 0;

  if (Sys.ie) browser = 'IE: ' + Sys.ie;
  if (Sys.firefox) browser = 'Firefox: ' + Sys.firefox;
  if (Sys.chrome) browser = 'Chrome: ' + Sys.chrome;
  if (Sys.opera) browser ='Opera: ' + Sys.opera;
  if (Sys.safari) browser = 'Safari: ' + Sys.safari;

  return browser
}

function get_parent(element, level, type) {
  while (level-- > 0) {
    element = element.parentElement;
  }
  if (type == 'i') {
    return element.rowIndex;
  } else if (type == 'id') {
    return element.id;
  } else if (type == 'object') {
    return element
  }
}


function header_traduction(trad, tableID) {
  let table = document.getElementById(tableID)

  for (var i=0; i < trad.length;i++) {
    table.rows[0].cells[i].innerHTML = trad[i]
  }
}

function fadingRedFieldOnError(elm) {
  elm.value = '';
  var color = 255;
  const colorFade = setInterval(() => {
    var c = color.toString();
    elm.style.borderColor = 'rgb('+c+',0,0)';
    if (color == 150) {
      elm.style.borderColor = '#fef84c';
      clearInterval(colorFade);
    }
    color -= 5 ;
  }, 150);
}
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
  inp.setAttribute('autocomplete','off');
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

function redirect_inventory(object) {
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
// CONTAINS ALL CLIENT AND SOCKET EVENTS FOR LOBBY 



// CLIENT EVENTS
////////////////////////////////////////////////////////////////////////////////////
asmbl_btn.onclick = function() {
  let table = document.getElementById('room-verify-listing');
  let box = Array.from(table.getElementsByClassName('check'));
  let crit = mapAssemblySelectors(table, box);
  handleAssemblyErrors(crit[0], crit[1], crit[2], crit[3], crit[4]);
}

checkAll.onclick = function() {
  let table =  document.getElementById('room-listing');
  let rows = table.getElementsByTagName('tr');
  let allChecked = checkTheBox(rows, false);
  if (allChecked == true) {
    checkTheBox(rows, true);
  }
}

del_btn.onclick = function() {
  let checked = getChecked();
  let index = checked[0];
  let ids = checked[1];

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
  let checked = getChecked();
  let index = checked[0];
  let ids = checked[1];

  if (index.length > 0) {
    for (const id of ids) {
      socket.emit('reset_room', id);
    }
    uncheckTheBox()

  } else {
    getErrorBox('errorBox', 
                'errorText', 
                'solid 3px red', 
                `<strong>Vous devez selectionner un/des salons</strong>`,
                1500);
  }
}

qCodeBtn.addEventListener('click', () => {
  let domain = window.location.origin;
  let checked = getChecked();
  let index = checked[0];
  let ids = checked[1];

  if (index.length > 0) {
    socket.emit('generate-qrcode-pdf', {'origin': domain, 
                'room_ids': ids});
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
    emitRoomCreation(context, type, name, id)
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

socket.on('grant_permission', () => {
  console.log('grant permission')
  verifySection.hidden = false;
  historicSection.hidden = false;
  roomManagement.hidden = false;
  roomAssembler.hidden = false;
  create_btn.disabled = false;
  del_btn.disabled = false;
  reset_btn.disabled = false;
  asmbl_btn.disabled = false;
});

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

// QRCODE 
socket.on('get-qrcode-pdf', (context) => {
  let buffer = context.pdf;
  let pdfWindow = window.open("");
  pdfWindow.document.write(
      "<iframe width='100%' height='100%' src='data:application/pdf;base64, " +
      encodeURI(buffer) + "'></iframe>"
  );
});
///////////////////////////////////////////////////////////////////////////////////////////////////////
  
