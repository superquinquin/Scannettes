// ALL SOCKET.IO EVENTS RECEIVED FROM FLASK-SOCKET.IO SERVER
// CONTAINS ALL CLIENT GENERATED EVENTS

// INIT
////////////////////
socket.on("connection", (socket) => {
  socket.join(roomID);
  socket.emit('message', 'has joined room:'+roomID);
});

socket.on('connect', function() {
  socket.emit('message', {data: 'I\'m connected!'});
  socket.emit('verify_connection', {'suffix': suffix, 'roomID': roomID, 'browser_id': browser});
});

socket.on('load_existing_room', function(context) {
  if (!charged) {
    //header
    const roomName = document.getElementById('room-name');
    roomName.textContent = 'Salon : ' + context.room_name;

    const purchaseName = document.getElementById('purchase-name');
    if (context.purchase_supplier == 'none') {
      const pur = context.purchase_name;
      purchaseName.textContent = 'Commande : ' + pur;

    } else {
      const pur = context.purchase_name + ' - ' + context.purchase_supplier;
      purchaseName.textContent = 'Commande : ' + pur;
    }

    // QUEUE
    let queueRecords = context.queue_records;
    fill_table("scanned-list", context, queueRecords, admin)

    // PURCHASED
    let purchasedRecords = context.entries_records
    fill_table("purchased-list", context, purchasedRecords, admin)

    // DONE
    let doneRecords = context.done_records;
    fill_table("verified-list", context, doneRecords, admin)

    CloseCModal();
    canvasDimension();
    scannedProductPlacement();
    updateRemainingProdcutToScan();
  }
});

socket.on('grant_permission', () => {
  console.log('grant permission')
  admin = true;
  if (get_state()== 'open') {
    admin_open_room_setup()
  } else if (get_state()== 'close') {
    closed_room_setup()
  } else {
    // room is done
    done_room_setup()
  }
  socket.emit('join_room', roomID);
});
///////////////////////////////////////////////////////////


// redirecting event
// REDIRECTING ON DENIED ACCESS
//////////////////////////////////////////////////////////////////////////////////////////////////////////
socket.on('task-access-denied', function(context) {
  console.log('redirecting to access denied screen')
  
  window.scrollTo(0, window.scrollY); 
  document.getElementById('confirmation-hub-modal').style.top = (window.scrollY - 5).toString() + 'px';
  document.getElementById('confirmation-hub-modal').style.display = 'flex';
  document.getElementById('html').style.overflowY = 'hidden';
  document.getElementById('heading-message').innerHTML = 'Permission refusée';
  document.getElementById('content-message').innerHTML = "Vous n'avez pas accès a cette fonctonnalité";


  // user has touched to html template to access features;
  // reloading to re init the template
  document.getElementById('accept-confirmation').setAttribute('onclick','window.location.reload()')
  document.getElementById('cancel-confirmation').setAttribute('onclick','window.location.reload()')
});

socket.on('denied_permission', () => {
  socket.emit('join_room', roomID);
});

socket.on('no_access_redirection', (context) => {
  window.location = context.url
});
/////////////////////////////////////////////////////////////////////////////////////////////////////////


// LOCAL & BROADCASTED DIRECT TABLE INTERACTIONS
///////////////////////////////////////////////////////////////////////////
socket.on('broadcast-block-wrong-item', function(context) {
  if (roomID == context.roomID) {
    let container = document.getElementById(context.tableID);
    let product = container.getElementsByClassName('product')[context.index];
    let namePanel = product.getElementsByClassName('panel-question-name')[0];
    let qtyPanel = product.getElementsByClassName('panel-question-qty')[0];

    product.setAttribute('style','background-color: #ff7866;');
    namePanel.style.display = 'none';
    qtyPanel.style.display = 'none';
  }
});


socket.on('broadcast_update_table_on_edit', function(context) {
  if (roomID == context.roomID) {
    let tableID = translateTableID(context.table);
    let table = document.getElementById(tableID);
    let product = table.getElementsByClassName('product')[context.index];
    let receiver = product.getElementsByClassName('received-qty')[0];

    if (context.type == 'mod') {
      receiver.innerHTML = '<strong>Reçue : </strong> &#xA0 ' + context.newqty;
    }

    if (tableID != 'verified-list') {
      // apply change to done table
      let productData = getRecordData(product)
      productData.scanned = context.scanned;
      productData.new = context.new;
      productData.mod = context.mod;

      removeFromTableWithEan(table, context.barcode);
      CreateProductBubble(productData, 'verified-list', admin);
      // search for multiple copies to remove.
      RemoveFromScannerContainer('scanned-list',productData.barcode, productData.product_id);
      RemoveFromScannerContainer('scanned-laser-list', productData.barcode, productData.product_id);
      RemoveFromScannerContainer('scanned-item-modal', productData.barcode, productData.product_id);
      updateRemainingProdcutToScan();

    } else {
      product.setAttribute('style','background-color: #ff9f40;');
      product.getElementsByClassName('mod-input-block')[0].style.display = 'none';
    }
  }
});

socket.on('move_product_to_queue', function(context) {
  //find product on entry table, append it to queue
  if (roomID == context.room_id) {
    let purchasedTable = document.getElementById('purchased-list');
    if (context.new_item) {
      // new item: add row in queue table
      CreateProductBubble(context, 'scanned-list', admin);

    } else {
      // search in entry table
      removeFromTableWithEan(purchasedTable, context.barcode);
      CreateProductBubble(context, 'scanned-list', admin);
    }
  }
  doubleScanBlocker = false;
});

socket.on('modify_scanned_item', function(context) {
  //  open modal for scanner to modify product without living camera mode
  let modal = document.getElementById('scanned-item-modal');
  CreateProductBubble(context, 'scanned-item-modal', admin);
  modal.style.display = 'flex';
});

socket.on('modify_scanned_laser_item', function(context) {
  //  open modal for scanner to modify product without living camera mode
  CreateProductBubble(context, 'scanned-laser-list', admin);
});

socket.on('broadcasted_deleted_item', function(context) {
  if (roomID == context.roomID) {
    let tableID = translateTableID(context.fromTable); 
    let index = context.index;
    let container = document.getElementById(tableID);
    let items = container.getElementsByClassName('product');

    for (var i = index.length - 1; i >= 0; i--) {
      items[index[i]].remove();
    }
    updateRemainingProdcutToScan();
    emptyPlaceholder(tableID);
  }
});
///////////////////////////////////////////////////////////////////////////////////////

// LOCAL AND BROADCASTED ROOM INTERACTIONS
//////////////////////////////////////////////////////////////////////////////////////

finisher.onclick = function () {
  openCModal('Fin de réception',
    'Veuillez confirmer la fin de réception.',
    'ClosingRoom()',
    false
  );
} 

suspender.onclick = function () {
  openCModal('Suspendre la réception',
    'Veuillez confirmer la suspension de la réception.',
    'suspendingRoom()',
    false
  );
}

verifier.onclick = function () {
  openCModal('Validation de la réception',
    "Confirmer l'envoie des données vers ODOO",
    'ValidatingRoom()',
    true
  );
}

recharger.onclick = function () {
  if (suffix.match('type%3Dpurchase')) {
    openCModal('Rechargement des données',
      "Veuillez confirmer le rechargement des données",
      'rechargingRoom()',
      false
    );
  } else if (suffix.match('type%3Dinventory')) {
    openCModal('Nullification',
      "Souhaitez vous nullifier les quantités non validées?",
      'nullification()',
      false
    );
  }
}

socket.on('broacasted_finish', function(context) {
  if (roomID == context.roomID) {
    window.location = context.url
  }
});

socket.on('broacasted_suspension', function(context) {
  if (roomID == context.roomID) {
    CloseCModal()
    window.location = context.url
  }
});

socket.on('reload-on-recharge', function(context) {
  CloseCModal()
  window.location.reload()
});


socket.on('broadcast-recharge', function(context) {
  if (roomID == context.roomID) {
    openCModal('Rechargement des données',
      "Des modifications ont été apportées depuis Odoo. Voulez vous recharger la page ?",
      'window.location.reload()',
      false
    );
  }
});

socket.on('broadcast-nullification', function(context) {
  if (roomID == context.roomID) {
    const queue = document.getElementById('scanned-list');
    let product_list = queue.getElementsByClassName('product');
    for (const product of product_list) {
      let record = getRecordData(product);
      record.qty_received = 0;
      record.new = context.new;
      record.mod = context.mod;
      CreateProductBubble(record, 'verified-list', admin)
    }
    queue.innerHTML = '';

    const entries = document.getElementById('purchased-list');
    product_list = entries.getElementsByClassName('product');
    for (const product of product_list) {
      let record = getRecordData(product);
      record.qty_received = 0;
      record.new = context.new;
      record.mod = context.mod;
      CreateProductBubble(record, 'verified-list', admin)
    }
    entries.innerHTML = '';
    CloseCModal()
  }
});

socket.on('update_on_assembler', function(context) {
  if (roomID == context.id) {
    window.location.reload()
  }
});

socket.on('close-room-on-validation', function(context) {
  if (roomID == context.roomID) {
    RemoveAutovalModule();
    CloseCModal();
    window.location = context.url;
  }
});

socket.on('close-test-fail-error-window', function(context) {
  if (roomID == context.roomID) {
    let errors = context.errors;

    RemoveAutovalModule();
    rescaleCModalContainer("open");
    document.getElementById('cancel-confirmation').hidden = false;
    document.getElementById('accept-confirmation').hidden = false;

    if (context.failed  == 'odoo_exist') {
      document.getElementById('heading-message').innerHTML = 'Oups des problèmes sont survenu avec certains produits';
      document.getElementById('content-message').innerHTML = "<strong>Produits inexistants sur odoo, ou problème de code-barre:</strong><br>" + errors;

    } else if (context.failed == 'purchase_exist') {
      document.getElementById('heading-message').innerHTML = 'Oups des produits sont inexistant dans la commande Odoo';
      document.getElementById('content-message').innerHTML = "<strong>Veuillez rajouter les produits suivants dans la commande associée :</strong><br>" + errors;
    } else if (context.failed == 'validation_exist') {
      document.getElementById('heading-message').innerHTML = 'Oups cette commande à déjà été validée';
      document.getElementById('content-message').innerHTML = "<strong>Il semble que la commande soit déjà validée</strong>.<br>Vous n'avez rien a faire, le salon disparaitra lors de la prochaine mise à jour";
    } else if (context.failed == 'inv_row') {
      document.getElementById('heading-message').innerHTML = 'Oups un problème est survenu';
      document.getElementById('content-message').innerHTML = "<strong>Il n'a pas été possible de créer l'inventaire dans Odoo</strong>.<br>veuillez réessayer plus tard.";
    } else if (context.failed == "inv_line_row") {
      document.getElementById('heading-message').innerHTML = 'Inventaire produit déjà existant...';
      document.getElementById('content-message').innerHTML = "<strong>Les produits suivant sont déjà en cours d'inventaire.</strong><br>Veuillez suprimer les anciennes instances d'inventaire ainsi que celle ci avant de recommencer le processus :<br>" + errors;
    }
    document.getElementById('accept-confirmation').setAttribute('onclick','CloseCModal()');
  }
});
/////////////////////////////////////////////////////////////////////////////////////////////

// WINDOWS ENVENTS
///////////////////////////////////////////////////////////////////
window.addEventListener('resize', canvasDimension);
function canvasDimension() {
  let canvas = document.getElementById('canvas')
  let width = window.innerWidth
  let height = window.innerHeight

  if (width > height) {
    canvas.style.width = '50%'
  } else {
    canvas.style.width = '100%'
  }
}

window.addEventListener('resize', scannedProductPlacement);
function scannedProductPlacement() {
  let bubble = document.getElementById('scanned-item-modal');

  let width = window.innerWidth
  let height = window.innerHeight
  bubble.style.left = ((width / 2) - ((width * 0.99) / 2)).toString() + 'px';
  bubble.style.width = (width * 0.99).toString() + 'px';
}

window.addEventListener('scroll', function() {
  let scrollHeight = window.scrollY;

  if (scrollHeight >= 500) {
    document.getElementById('toTop').style.display = 'flex';
    document.getElementById('toTop').style.top = (scrollHeight + 10).toString() + 'px';
  } else {
    document.getElementById('toTop').style.display = 'none';
  }
});

function scrolltop() {
  window.scrollTo(0, 0);
}

// collapse or close queue, entries and done containers event
const collapser = document.getElementsByClassName("collaps-block");
for (var i = 0; i < collapser.length; i++) {
  collapser[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    var delBtn = content.nextElementSibling;
    if (content.style.display == 'flex'){
      content.style.display = 'none';
      if (admin) {
        delBtn.hidden = true;
      }

    } else {
      content.style.display = 'flex';
      if (admin) {
        delBtn.hidden = false;
      }
    } 
  });
}
///////////////////////////////////////////////////////////////////