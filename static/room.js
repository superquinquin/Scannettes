
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
    socket.emit('verify_connection', suffix)
  }
});

socket.on('load_existing_room', function(context) {
  //header
  roomName.textContent += context.room_name;
  purchaseName.textContent += context.purchase_name;
  // tables
  queueTableContainer.innerHTML += context.queue_table
  append_mod_column('dataframe queue_table')
  entriesTableContainer.innerHTML += context.entries_table
  append_mod_column('dataframe entry_table')
  doneTableContainer.innerHTML += context.done_table
  append_mod_column('dataframe done_table')

});

socket.on('grant_permission', () => {
  console.log('grant permission')
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
      append_row(context)
      update_mod_btn_id(QueueTable, 'dataframe queue_table');
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



// FUNCTIONS
function append_mod_column(tableID) {
  let table = document.getElementById(tableID);
  let tr = Array.from(table.getElementsByTagName('tr'));
  for (const [i, r] of tr.entries()) {
    if (i == 0) {
      let newHead = document.createElement('th');
      newHead.innerHTML = 'Modification';
      tr[i].appendChild(newHead);
    } else {
      let newCell = document.createElement('td')
      let inp = document.createElement('input')
      inp.setAttribute('type', 'text');
      inp.setAttribute('class', 'mod-input');
      newCell.appendChild(inp);
      let btn = document.createElement("button");
      btn.setAttribute('id',i+'#'+tableID);
      btn.setAttribute('class', 'mod_received-btn');
      btn.setAttribute('onclick','change_qty(this.id)');
      btn.appendChild(document.createTextNode('mod'));
      newCell.appendChild(btn);
      tr[i].appendChild(newCell);
    }
  }
}

function append_row(context) {
  let queue = document.getElementById('dataframe queue_table');
  let row = document.createElement('tr');

  let barcode = document.createElement('td');
  barcode.innerHTML = context.code_ean;
  row.appendChild(barcode)

  let id = document.createElement('td');
  id.innerHTML = context.product_id;
  row.appendChild(id)

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
  row.appendChild(qty_received);

  let edit_cell = document.createElement('td');
  let inp = document.createElement('input')
  inp.setAttribute('type', 'text');
  inp.setAttribute('class', 'mod-input');
  edit_cell.appendChild(inp);
  let btn = document.createElement("button");
  btn.setAttribute('id',0+'#'+'dataframe queue_table');
  btn.setAttribute('class', 'mod_received-btn');
  btn.setAttribute('onclick','change_qty(this.id)');
  btn.appendChild(document.createTextNode('mod'));
  edit_cell.appendChild(btn); 
  row.appendChild(edit_cell);     

  queue.appendChild(row);  
}


function draw_corner(X,Y, len, place) {
  ctx.beginPath();

  ctx.moveTo(X, Y);
  if (place === 'bottomleft' || place === 'bottomright') {
    ctx.lineTo(X, Y - len);
  } else {
    ctx.lineTo(X, Y + len);
  }

  ctx.moveTo(X, Y);
  if (place === 'topright' || place === 'bottomright') {
    ctx.lineTo(X - len, Y);
  } else {
    ctx.lineTo(X + len, Y);
  }
  ctx.stroke();
}


function get_suffix(url) {
  let array = url.split('%26id%3D');
  if (array.length > 1) {
    suffix = array[array.length - 1];
    roomID = array[0].split('/')[array[0].split('/').length - 1];
  } else {
    suffix = roomID = url.split('/')[url.split('/').length - 1];
  }
  return roomID, suffix;
}




function change_qty(id) {
  let index = id.split('#')[0];
  let table_id = id.split('#')[1];
  let table = document.getElementById(table_id);
  let row = table.rows[index];

  let receiver = table.rows[index].cells[5];    
  let input = table.rows[index].cells[6].getElementsByClassName('mod-input').item(0);
  let barcode = table.rows[index].cells[0].innerHTML;
  let product_id = table.rows[index].cells[1].innerHTML;
  let newQty = input.value;

  if (/^\d+\.\d+$|^\d+$/.test(newQty)) {
    receiver.innerHTML = newQty;
    input.value = '';
  
    context = {'roomID': roomID,
              'table': table_id,
              'index': index, 
              'newqty': newQty, 
              'barcode': barcode, 
              'product_id': product_id};
    socket.emit('update_table', context);
  
    //add row in done table
    if (table_id != 'dataframe done_table') {
      // apply change to done table
      let doneTable = document.getElementById('dataframe done_table');
      doneTable.appendChild(row);
      update_mod_btn_id(doneTable, 'dataframe done_table');
      //apply change to from_table
      update_mod_btn_id(table, table_id);
    }  

  } else {
    input.value = '';
    var color = 255;
    const colorFade = setInterval(() => {
      var c = color.toString();
      input.style.borderColor = 'rgb('+c+',0,0)';
      if (color == 150) {
        input.style.borderColor = 'black'
        clearInterval(colorFade);
      }
      color -= 5 ;
    }, 150);
  }

}



function update_mod_btn_id(htmlTable, tableID) {
  let tr = Array.from(htmlTable.getElementsByTagName('tr'));
    for (const [i, r] of tr.entries()) {
      if (i > 0) {
        let btn = r.getElementsByClassName('mod_received-btn').item(0);
        btn.id = i+'#'+tableID;
      }
    }
}



socket.on('broadcast_update_table_on_edit', function(context) {
  // move table
  // change id
  // change received value
  console.log('update')
  console.log(context.roomID)
  if (roomID == context.roomID) {
    // having problem with room "connection event" force to check roomID to accept broadcasted values
    //to be solved
    let index = context.index;
    let table_id = context.table;
    let table = document.getElementById(table_id);
    let row = table.rows[index];
    let receiver = table.rows[index].cells[5];  
    let newQty = context.newqty;
    receiver.innerHTML = newQty;
    if (table_id != 'dataframe done_table') {
      // apply change to done table
      let doneTable = document.getElementById('dataframe done_table');
      doneTable.appendChild(row);
      update_mod_btn_id(doneTable, 'dataframe done_table');
      //apply change to from_table
      update_mod_btn_id(table, table_id);
    }
  }
});