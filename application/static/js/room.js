
var browser = get_browser_id()
var roomID;
var suffix;
const currentLoc = window.location.href;
roomID, suffix = get_suffix(currentLoc)

const socket = io.connect(config.address);

const roomName = document.getElementById('room-name');
const purchaseName = document.getElementById('purchase-name');
const queueTableContainer = document.getElementById('Queue-table');
const entriesTableContainer = document.getElementById('entries-table');
const doneTableContainer = document.getElementById('done-table');

// OPTION MODAL (solo mod)
const option = document.getElementById("option-colapse");
const soloMode = document.getElementById('solo-mode')

// ADD ITEMS MODAL
const addItem = document.getElementById('add-colapse');
const cancelAddItem = document.getElementById('cancel-add-btn')
const acceptAddItem = document.getElementById('accept-add-btn')

// DELETE ITEMS
const delQueue = document.getElementById('del-from-queue');
delQueue.hidden = true;
delQueue.disabled = true;
const delDone = document.getElementById('del-from-done');
delDone.hidden = true;
delDone.disabled = true;

//MODIFICATION MODAL
// IN QUEUE TABLE
const modQeueModalBtn = document.getElementById('mod-from-queue')
modQeueModalBtn.hidden = true;
const modQueueElement = document.getElementById('mod-from-queue')
const cancelModQueue = document.getElementById('cancel-modQueue-btn')
const acceptModQueue = document.getElementById('accept-modQueue-btn')
// IN DONE TABLE
const modDoneModalBtn = document.getElementById('mod-from-done')
modDoneModalBtn.hidden = true;
const modDoneElement = document.getElementById('mod-from-done')
const cancelModDone = document.getElementById('cancel-modDone-btn')
const acceptModDone = document.getElementById('accept-modDone-btn')

//CLOSING
const adminClose = document.getElementById('admin-close')
adminClose.hidden = true;
const finisher = document.getElementById('closing-room');
const suspender = document.getElementById('room-suspension');
suspender.disabled = true;
const verifier = document.getElementById('admin-validation');
verifier.disabled = true;


// ON CONNECTION
socket.on("connection", (socket) => {
  console.log('joining room')
  socket.join(roomID);
  socket.emit('message', 'has joined room:'+roomID);
});

socket.on('connect', function() {
  console.log('has connected');
  socket.emit('message', {data: 'I\'m connected!'});
  socket.emit('join_room', roomID);
  if (suffix.slice(0,4) != 'room') {
    console.log('verify permissions')
    socket.emit('verify_connection', {'suffix': suffix, 'browser_id': browser})
  }
});

socket.on('load_existing_room', function(context) {
  //header
  roomName.textContent += context.room_name;
  purchaseName.textContent += context.purchase_name;
  // tables
  queueTableContainer.innerHTML += context.queue_table
  append_mod_column('dataframe queue_table')
  header_traduction(['Select','Code barre', 'ID', 'Nom', 'Quantité','Unités par emballage', 'Reçu', 'Modification'], 'dataframe queue_table')
  check_empty_table('dataframe queue_table')
  entriesTableContainer.innerHTML += context.entries_table
  append_mod_column('dataframe entry_table')
  header_traduction(['Select','Code barre', 'ID', 'Nom', 'Quantité','Unités par emballage', 'Reçu', 'Modification'], 'dataframe entry_table')
  check_empty_table('dataframe entry_table')
  doneTableContainer.innerHTML += context.done_table
  append_mod_column('dataframe done_table')
  header_traduction(['Select','Code barre', 'ID', 'Nom', 'Quantité','Unités par emballage', 'Reçu', 'Modification'], 'dataframe done_table')
  check_empty_table('dataframe done_table')

});

socket.on('grant_permission', () => {
  console.log('grant permission')
  delQueue.hidden = false;
  delQueue.disabled = false;
  delDone.hidden = false;
  delDone.disabled = false;
  modQeueModalBtn.hidden = false;
  modDoneModalBtn.hidden = false;
  adminClose.hidden = false;
  suspender.disabled = false;
  verifier.disabled = false;
});



socket.on('move_product_to_queue', function(context) {
  //find product on entry table
  // append it to queue table
  
  let scannedEan = context.code_ean
  let newItem = context.new_item
  let QueueTable = document.getElementById('dataframe queue_table')

  if (roomID == context.room_id) {
    if (newItem) {
      // new item: add row in queue table
      append_row(context, 'dataframe queue_table')
    } else {
      // search in entry table
      let table = document.getElementById('dataframe entry_table');
      let tr = Array.from(table.getElementsByTagName('tr'));
      for (const [i, r] of tr.entries()) { 
        let entryEan = table.rows[index].cells[0]; 
        if (entryEan == scannedEan) {
          // move row from entries to queue
          let row = table.rows[i];
          QueueTable.appendChild(row);
        }
      }
    }
  }
});



socket.on('broadcast_update_table_on_edit', function(context) {
  // move table
  // change id
  // change received value
  console.log('update')
  console.log(context.roomID)
  if (roomID == context.roomID) {
    // having problem with room "connection event" force to check roomID to accept broadcasted values
    //to be solved
    let type = context.type
    let index = context.index;
    let table_id = context.table;
    let table = document.getElementById(table_id);
    let row = table.rows[index];
    let receiver = table.rows[index].cells[6];
    
    if (type == 'mod') {
      let newQty = context.newqty;
      receiver.innerHTML = newQty;
    }

    if (table_id != 'dataframe done_table') {
      // apply change to done table
      let doneTable = document.getElementById('dataframe done_table');
      row.getElementsByClassName('val_received-btn').item(0).remove();
      doneTable.appendChild(row);
    }
  }
});


// FUNCTIONS
function append_mod_column(tableID) {
  /**
  * while loading the prewritten tables, add :
  * select checkbox; validation button on status quo received qty; modification collumn
  */
  let table = document.getElementById(tableID);
  let tr = Array.from(table.getElementsByTagName('tr'));
  for (const [i, r] of tr.entries()) {
    if (i == 0) {
      let newSelect = document.createElement('th');
      newSelect.innerHTML = 'Select'
      tr[i].insertBefore(newSelect, tr[i].querySelectorAll("th")[0]);

      let newHead = document.createElement('th');
      newHead.innerHTML = 'Modification';
      tr[i].appendChild(newHead);
    } else {
      // select checkbox
      let newCheck = document.createElement('td')
      let checkBox = document.createElement('input')
      checkBox.setAttribute('type','checkbox')
      checkBox.setAttribute('class','check')
      newCheck.appendChild(checkBox);
      tr[i].insertBefore(newCheck, tr[i].querySelectorAll("td")[0]);  

      if (tableID != 'dataframe done_table') {
        // validation btn to verify status quo
        let valBtn = document.createElement('button')
        valBtn.setAttribute('id',i+'#'+tableID+'#val');
        valBtn.setAttribute('class', 'val_received-btn');
        valBtn.setAttribute('onclick',"change_qty(this.id, get_parent_id(this, 2, 'i'), get_parent_id(this, 4, 'id'), 'val')");
        valBtn.style.float = 'right'
        valBtn.appendChild(document.createTextNode('✓'));
        tr[i].querySelectorAll("td")[6].appendChild(valBtn)
      }

      // modification box
      let newCell = document.createElement('td')
      let inp = document.createElement('input')
      inp.setAttribute('type', 'text');
      inp.setAttribute('class', 'mod-input');
      newCell.appendChild(inp);
      let btn = document.createElement("button");
      btn.setAttribute('id',i+'#'+tableID+'#mod');
      btn.setAttribute('class', 'mod_received-btn');
      btn.setAttribute('onclick',"change_qty(this.id, get_parent_id(this, 2, 'i'), get_parent_id(this, 4, 'id'), 'mod')");
      btn.appendChild(document.createTextNode('mod'));
      newCell.appendChild(btn);
      tr[i].appendChild(newCell);
    }
  }
}

function append_row(context,tableID) {
  let table = document.getElementById(tableID);
  let row = document.createElement('tr');

  let select = document.createElement('td');
  let checkBox = document.createElement('input');
  checkBox.setAttribute('type','checkbox');
  checkBox.setAttribute('class','check');
  select.appendChild(checkBox);
  row.appendChild(select);

  let barcode = document.createElement('td');
  barcode.innerHTML = context.code_ean;
  row.appendChild(barcode);

  let id = document.createElement('td');
  id.innerHTML = context.product_id;
  row.appendChild(id);

  let name = document.createElement('td');
  name.innerHTML = context.product_name;
  row.appendChild(name);

  let qty = document.createElement('td');
  qty.innerHTML = context.product_qty;
  row.appendChild(qty);

  let pckg_qty = document.createElement('td');
  pckg_qty.innerHTML = context.product_pkg_qty;
  row.appendChild(pckg_qty);

  let qty_received = document.createElement('td');
  qty_received.innerHTML = context.product_received_qty;
  if (tableID == 'dataframe queue_table') {
    let valBtn = document.createElement('button')
    valBtn.setAttribute('id',0+'#'+tableID+'#val');
    valBtn.setAttribute('class', 'val_received-btn');
    valBtn.setAttribute('onclick',"change_qty(this.id, get_parent_id(this, 2, 'i'), get_parent_id(this, 4, 'id'), 'val')");
    valBtn.style.float = 'right'
    valBtn.appendChild(document.createTextNode('✓'));
    qty_received.appendChild(valBtn)
  }
  row.appendChild(qty_received);

  let edit_cell = document.createElement('td');
  let inp = document.createElement('input')
  inp.setAttribute('type', 'text');
  inp.setAttribute('class', 'mod-input');
  edit_cell.appendChild(inp);
  let btn = document.createElement("button");
  btn.setAttribute('id',0+'#'+tableID+'#mod');
  btn.setAttribute('class', 'mod_received-btn');
  btn.setAttribute('onclick',"change_qty(this.id, get_parent_id(this, 2, 'i'), get_parent_id(this, 4, 'id'), 'mod')");
  btn.appendChild(document.createTextNode('mod'));
  edit_cell.appendChild(btn); 
  row.appendChild(edit_cell);     

  table.appendChild(row);  
}






function change_qty(id, index, tableID, type) {
  let table = document.getElementById(tableID);
  let row = table.rows[index];

  let receiver = table.rows[index].cells[6];    
  let barcode = table.rows[index].cells[1].innerHTML;
  let product_id = table.rows[index].cells[2].innerHTML;

  if (type == 'mod') {
    let input = table.rows[index].cells[7].getElementsByClassName('mod-input').item(0);
    let newQty = input.value;
  
    if (/^\d+\.\d+$|^\d+$/.test(newQty)) {
      receiver.innerHTML = newQty;
      input.value = '';
    
      context = {'roomID': roomID,
                'table': tableID,
                'index': index, 
                'newqty': newQty, 
                'barcode': barcode, 
                'product_id': product_id,
                'type': 'mod'};
      socket.emit('update_table', context);
    
      //add row in done table
      if (tableID != 'dataframe done_table') {
        // apply change to done table
        let doneTable = document.getElementById('dataframe done_table');
        doneTable.appendChild(row);
      }  
  
    } else {
      input.value = '';
      var color = 255;
      const colorFade = setInterval(() => {
        var c = color.toString();
        input.style.borderColor = 'rgb('+c+',0,0)';
        if (color == 150) {
          input.style.borderColor = '#fef84c';
          clearInterval(colorFade);
        }
        color -= 5 ;
      }, 150);
    }

  } else {
    context = {'roomID': roomID,
              'table': tableID,
              'index': index,
              'newqty': null,
              'barcode': barcode, 
              'product_id': product_id,
              'type': 'val'};
    socket.emit('update_table', context);

    let doneTable = document.getElementById('dataframe done_table');
    row.getElementsByClassName('val_received-btn').item(0).remove();
    doneTable.appendChild(row);

  }
}




function get_suffix(url) {
  let array = url.split('%26id%3D');
  if (array.length > 1) {
    suffix = '%26id%3D' + array[array.length - 1];
    roomID = array[0].split('/')[array[0].split('/').length - 1];
  } else {
    suffix = roomID = url.split('/')[url.split('/').length - 1];
  }
  return roomID, suffix;
}







// OPTION MODAL
option.onclick = function () {
  let content = document.getElementById('option-content');
  if (content.style.display === "block") {
    content.style.display = "none";
  } else {
    content.style.display = "block";
  }
}

// ADD ITEM MODAL
addItem.onclick = function() {
  let content = document.getElementById('added-item-content');
  if (content.style.display === "block") {
    content.style.display = "none";
  } else {
    content.style.display = "block";
  }
}


cancelAddItem.onclick = function () {
  let inp = document.getElementsByClassName('add-input');
  let content = document.getElementById('added-item-content');
  for (var i = 0; i<inp.length; i++) {
    inp[i].value = "";
  }
  content.style.display = "none";
}


acceptAddItem.onclick = function () {
  let content = document.getElementById('added-item-content');
  let barcode = document.getElementById('add-barcode').value;
  let id = document.getElementById('add-id').value;
  let name = document.getElementById('add-name').value;
  let received_qty = document.getElementById('add-received').value;
  context = {'code_ean':barcode, 'product_id':id, 'product_name':name, 'product_received_qty':received_qty,
             'product_qty': 0, 'product_pkg_qty': 0, 'roomID': roomID};
  append_row(context, 'dataframe done_table');

  document.getElementById('add-barcode').value = "";
  document.getElementById('add-id').value = "";
  document.getElementById('add-name').value = "";
  document.getElementById('add-received').value = "";
  content.style.display = "none";

  socket.emit('add-new-item', context);
}

socket.on('broadcasted_added_item', function(context) {
  if (roomID == context.roomID) {
    append_row(context, 'dataframe done_table');
  }
});


// DELETE ITEMS
function del_item(fromTable) {
  let index = [];
  let table = document.getElementById(fromTable);
  let box = Array.from(table.getElementsByClassName('check'));

  for (const [i, b] of box.entries()) {
    if (b.checked) {
      index.push(i + 1);
    }
  }
  context = {'index': index, 'roomID': roomID, 'fromTable': fromTable};
  socket.emit('del_item', context);
}

socket.on('broadcasted_deleted_item', function(context) {
  if (roomID == context.roomID) {
    let fromTable = context.fromTable
    let index = context.index
    let table = document.getElementById(fromTable)

    for (var i = index.length - 1; i >= 0; i--) {
      table.deleteRow(index[i]);
    }
  }
});

delQueue.onclick = function () {
  let fromTable = 'dataframe queue_table';
  del_item(fromTable);
}

delDone.onclick = function () {
  let fromTable = 'dataframe done_table';
  del_item(fromTable);
}


// MODIFICATION MODAL
// MODIFICATION IN QUEUE TABLE

function create_mod_modal(context) {
  let fromTable = context.fromTable
  let table = document.getElementById(fromTable);
  let content = document.getElementById(context.content);
  let box = Array.from(table.getElementsByClassName('check'));
  let index = [];

  for (const [i, b] of box.entries()) {
    if (b.checked) {
      index.push(i + 1);
    }
  }

  if (index.length > 1) {
    document.getElementById(context.errorBox).innerHTML = 'Veuillez sélectionner un seul produit';
  } else if (index.length == 0) {
    document.getElementById(context.errorBox).innerHTML = 'Veuillez sélectionner un produit';
  } else {
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      document.getElementById(context.errorBox).innerHTML = "";
      content.style.display = "block";
      document.getElementById(context.barcode).value = table.rows[index[0]].cells[1].innerHTML;
      document.getElementById(context.id).value = table.rows[index[0]].cells[2].innerHTML;
      document.getElementById(context.name).value = table.rows[index[0]].cells[3].innerHTML;
      document.getElementById(context.index).innerHTML = index[0];
    }
  }
}

function cancelMod(context) {
  let fromTable = context.fromTable
  let table = document.getElementById(fromTable);
  let content = document.getElementById(context.content);
  let box = Array.from(table.getElementsByClassName('check'));
  let index = document.getElementById(context.index).innerHTML;

  content.style.display = "none";
  document.getElementById(context.barcode).value = "";
  document.getElementById(context.id).value = "";
  document.getElementById(context.name).value = "";
  document.getElementById(context.index).innerHTML = "";
  box[index-1].checked = false;
}

function acceptMod(input) {
  let fromTable = input.fromTable
  let table = document.getElementById(fromTable);
  let content = document.getElementById(input.content);
  let box = Array.from(table.getElementsByClassName('check'));

  let index = document.getElementById(input.index).innerHTML;
  let barcode = document.getElementById(input.barcode).value;
  let id = document.getElementById(input.id).value;
  let name = document.getElementById(input.name).value;


  context = {'fromTable': fromTable, 'code_ean': barcode,
             'product_id': id, 'product_name': name,
             'index': index, 'roomID': roomID}
  socket.emit('mod_item', context)

  content.style.display = "none";
  document.getElementById(input.barcode).value = "";
  document.getElementById(input.id).value = "";
  document.getElementById(input.name).value = "";
  document.getElementById(input.index).innerHTML = "";
  box[index-1].checked = false;
}

socket.on('broadcasted_mod_item', function(context) {
  if (roomID == context.roomID) {
    let fromTable = context.fromTable;
    let table = document.getElementById(fromTable);
    let index = context.index;
    let barcode = context.code_ean;
    let id = context.product_id;
    let name = context.product_name;

    table.rows[index].cells[1].innerHTML = barcode;
    table.rows[index].cells[2].innerHTML = id;
    table.rows[index].cells[3].innerHTML = name;
  }
});


modQueueElement.onclick = function() {
  create_mod_modal({'fromTable': 'dataframe queue_table',
                    'errorBox': 'queue-error-msg',
                    'content': 'modQueue-item-content',
                    'barcode': 'modQueue-barcode',
                    'id': 'modQueue-id',
                    'name': 'modQueue-name',
                    'index': 'modQueue-index'})
}

cancelModQueue.onclick = function () {
  cancelMod({'fromTable': 'dataframe queue_table',
            'content': 'modQueue-item-content',
            'barcode': 'modQueue-barcode',
            'id': 'modQueue-id',
            'name': 'modQueue-name',
            'index': 'modQueue-index'})
}

acceptModQueue.onclick = function () {
  acceptMod({'fromTable': 'dataframe queue_table',
                    'content': 'modQueue-item-content',
                    'barcode': 'modQueue-barcode',
                    'id': 'modQueue-id',
                    'name': 'modQueue-name',
                    'index': 'modQueue-index'});
}

modDoneElement.onclick = function () {
  create_mod_modal({'fromTable': 'dataframe done_table',
                    'content': 'modDone-item-content',
                    'errorBox': 'done-error-msg',
                    'barcode': 'modDone-barcode',
                    'id': 'modDone-id',
                    'name': 'modDone-name',
                    'index': 'modDone-index'});
}

cancelModDone.onclick = function () {
  cancelMod({'fromTable': 'dataframe done_table',
            'content': 'modDone-item-content',
            'barcode': 'modDone-barcode',
            'id': 'modDone-id',
            'name': 'modDone-name',
            'index': 'modDone-index'});
}

acceptModDone.onclick = function () {
  acceptMod({'fromTable': 'dataframe done_table',
            'content': 'modDone-item-content',
            'barcode': 'modDone-barcode',
            'id': 'modDone-id',
            'name': 'modDone-name',
            'index': 'modDone-index'});
}


// CLOSING ACTION
suspender.onclick = function () {
  context = {'roomID': roomID, 'suffix': suffix}
  socket.emit('suspending_room', context)
}

socket.on('broacasted_suspension', function(context) {
  if (roomID == context.roomID) {
    window.location = context.url
  }
});

finisher.onclick = function () {
  context = {'roomID': roomID, 'suffix': suffix}
  socket.emit('finishing_room', context)
} 

socket.on('broacasted_finish', function(context) {
  if (roomID == context.roomID) {
    window.location = context.url
  }
});





function empty_table(tableID) {
  let table = document.getElementById(tableID)
  let row = document.createElement('tr');

  for (var i=0; i < 8; i++) {
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











