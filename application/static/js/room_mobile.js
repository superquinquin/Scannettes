
var browser = get_browser_id()
var roomID;
var suffix;
var admin =  false;
const currentLoc = window.location.href;
roomID, suffix = get_suffix(currentLoc)

const socket = io.connect(config.ADDRESS);

const adminClose = document.getElementById('admin-close');
const closing = document.getElementById('closing-room');
const aucdiv = document.getElementById('all-user-close');
const suspBlock = document.getElementById('suspension-block');
const verifBlock = document.getElementById('verif-block');
const rechargeBlock = document.getElementById('recharge-block');
const suspender = document.getElementById('room-suspension');
const verifier = document.getElementById('admin-validation');
const recharger = document.getElementById('room-recharge');
verifBlock.hidden = true;
adminClose.hidden = true;
verifier.disabled = true;
recharger.disabled = true;
suspender.disabled = true;

const delQueue = document.getElementById('del-from-queue');

//  ON SOCKET CONNECTION
socket.on("connection", (socket) => {
  console.log('joining room')
  socket.join(roomID);
  socket.emit('message', 'has joined room:'+roomID);
});

socket.on('connect', function() {
  console.log('has connected');
  socket.emit('message', {data: 'I\'m connected!'});
  // socket.emit('join_room', roomID);
  
  console.log('verify permissions')
  socket.emit('verify_connection', {'suffix': suffix, 'roomID': roomID, 'browser_id': browser})
});

socket.on('load_existing_room', function(context) {
  //header
  roomState = context.room_state
  const roomName = document.getElementById('room-name');
  roomName.textContent = 'Salon : ' + context.room_name;

  const purchaseName = document.getElementById('purchase-name');
  console.log(context.purchase_supplier)
  if (context.purchase_supplier == 'none') {
    const pur = context.purchase_name;
    purchaseName.textContent = 'Commande : ' + pur;

  } else {
    const pur = context.purchase_name + ' - ' + context.purchase_supplier;
    purchaseName.textContent = 'Commande : ' + pur;
  }

  CloseCModal()
  canvasDimension()
  scannedProductPlacement()

  // QUEUE
  let queueRecords = context.queue_records;
  emptyPlaceholder('scanned-list');
  for (const product of queueRecords) {
    product.scanned = context.scanned;
    product.new = context.new;
    product.mod = context.mod;
    CreateProductBubble(product, 'scanned-list', admin);
  }
  // PURCHASED
  let purchasedRecords = context.entries_records
  emptyPlaceholder('purchased-list');
  for (const product of purchasedRecords) {
    product.scanned = context.scanned;
    product.new = context.new;
    product.mod = context.mod;
    CreateProductBubble(product, 'purchased-list', admin);
  }
  // DONE
  let doneRecords = context.done_records;
  emptyPlaceholder('verified-list');
  for (const product of doneRecords) {
    product.scanned = context.scanned;
    product.new = context.new;
    product.mod = context.mod;
    CreateProductBubble(product, 'verified-list', admin);
  }

  updateRemainingProdcutToScan()
});



socket.on('grant_permission', () => {
  console.log('grant permission')
  admin = true;
  if (get_state()== 'open') {
    delQueue.hidden = false;
    adminClose.hidden = false;
    suspender.disabled = false;
    recharger.disabled = false;
  } else if (get_state()== 'close') {
    let purchaseDEL = document.getElementById('del-from-purchased')
    let verifiedDEL = document.getElementById('del-from-verfied')

    for (container of document.getElementsByClassName('container')) {
      container.style.display = 'flex';
      container.parentElement
              .getElementsByClassName('collaps-block')[0]
              .classList.toggle('active')
    }

    delQueue.hidden = false;
    adminClose.hidden = false;

    closing.disabled = true;
    aucdiv.hidden = true;

    suspBlock.hidden = true;
    verifBlock.hidden = false;
    
    verifier.disabled = false;
    recharger.disabled = false;

    purchaseDEL.hidden = false;
    verifiedDEL.hidden = false;

  } else {
    for (container of document.getElementsByClassName('container')) {
      container.style.display = 'flex';
      container.parentElement
              .getElementsByClassName('collaps-block')[0]
              .classList.toggle('active')
    }
    delQueue.hidden = true;
    adminClose.hidden = true;

    closing.disabled = true;
    aucdiv.hidden = true;

    suspBlock.hidden = true;
    verifBlock.hidden = true;
    
    verifier.disabled = true;
    recharger.disabled = true;

  }

  socket.emit('join_room', roomID);
});

socket.on('denied_permission', () => {
  socket.emit('join_room', roomID);
});

socket.on('no_access_redirection', (context) => {
  window.location = context.url
});







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




function NameVerificationY(element) {
  console.log('in Y')
  let product = element.parentElement.parentElement.parentElement;

  // changing question
  let panelName = product.getElementsByClassName('panel-question-name')[0];
  let panelQTY = product.getElementsByClassName('panel-question-qty')[0];
  panelName.style.display = 'none'
  panelQTY.style.display = 'flex'
}



function WrongProductConfirmation(element) {
  let product = element.parentElement.parentElement.parentElement;
  let producData = getRecordData(product)
  let tableID = product.parentElement.id
  window.scrollTo(0,0); 
  document.getElementById('confirmation-hub-modal').style.display = 'flex';
  document.getElementById('html').style.overflowY = 'hidden';
  document.getElementById('heading-message').innerHTML = 'Mauvais produit';
  document.getElementById('content-message').innerHTML = "Confirmer que le produit : <strong>"+producData.name+ "</strong> n'est pas le bon ou qu'il n'a pas été commandé ?";


  document.getElementById('accept-confirmation').setAttribute('onclick','NameVerificationN("'+tableID+'","'+producData.index.toString()+'")')
}

function NameVerificationN(tableID, index) {
  let product = (document.getElementById(tableID)
                  .getElementsByClassName('product')[index])
  let productData = getRecordData(product)
  
  context = {'roomID': roomID,
              'tableID': tableID,
              'barcode': productData.barcode, 
              'product_id': productData.id,
              'index': productData.index};

  socket.emit('block-product', context);
  CloseCModal()
}

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


function QtyVerificationY(element) {

  let product = element.parentElement.parentElement.parentElement;
  console.log(product)
  let productData = getRecordData(product)

  let tableID = correctTableID(productData.tableID)
  context = {'roomID': roomID,
              'table': tableID,
              'index': productData.index,
              'newqty': null,
              'barcode': productData.barcode, 
              'product_id': productData.id,
              'type': 'val'};
  console.log(context)
  socket.emit('update_table', context);
}

socket.on('broadcast_update_table_on_edit', function(context) {
  console.log('in update table on edit')
  if (roomID == context.roomID) {
    let type = context.type
    let index = context.index;
    let tableID = translateTableID(context.table);
    let table = document.getElementById(tableID);
    let product = table.getElementsByClassName('product')[index];
    let receiver = product.getElementsByClassName('received-qty')[0];

    
    if (type == 'mod') {
      receiver.innerHTML = '<strong>Reçue : </strong> &#xA0 ' + context.newqty;
    }

    if (tableID != 'verified-list') {
      // apply change to done table
      let productData = getRecordData(product)
      productData.scanned = context.scanned;
      productData.new = context.new;
      productData.mod = context.mod;
      console.log(productData)

      let productAray = table.getElementsByClassName('product');
      for (const product of productAray) {
        let ean = product.getElementsByClassName('code-barre')[0].innerHTML;
        if (ean == context.barcode) {
          product.remove();
          emptyPlaceholder(tableID)
        }
      }
      CreateProductBubble(productData, 'verified-list', admin);
      // search for multiple copies to remove.
      RemoveFromScannerContainer('scanned-list',productData.barcode, productData.product_id);
      RemoveFromScannerContainer('scanned-laser-list', productData.barcode, productData.product_id);
      RemoveFromScannerContainer('scanned-item-modal', productData.barcode, productData.product_id);

      updateRemainingProdcutToScan()
    } else {
      product.setAttribute('style','background-color: #ff9f40;')
      product.getElementsByClassName('mod-input-block')[0].style.display = 'none';
    }
  }
});

function RemoveFromScannerContainer(tableID, barcode, productId) {
  let container = document.getElementById(tableID);
  for (const product of container.getElementsByClassName('product')) {
    let id = product.getElementsByClassName('product-id')[0].innerHTML;
    let ean = product.getElementsByClassName('code-barre')[0].innerHTML;

    if ((id == productId & id != "0") || ean == barcode) {
      product.remove();
      if (tableID == 'scanned-item-modal') {
        document.getElementById('scanned-item-modal').style.display = 'none';
      } else {
        emptyPlaceholder(tableID);
      }
    }
  }
}

function acceptMod(element) {
  let product = element.parentElement.parentElement.parentElement;
  let productData = getRecordData(product);
  let tableID = correctTableID(productData.tableID);
  let receiver = product.getElementsByClassName('received-qty')[0];
  let input = product.getElementsByClassName('mod-input')[0];
  let newQty = input.value;


  if (/^\d+\.\d+$|^\d+$/.test(newQty)) {
    receiver.innerHTML = newQty;
    input.value = '';

    context = {'roomID': roomID,
                'table': tableID,
                'index': productData.index,
                'newqty': newQty,
                'barcode': productData.barcode, 
                'product_id': productData.id,
                'type': 'mod'};
                
    socket.emit('update_table', context);

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
}

function acceptModFromKey(element) {
  if (event.key === 'Enter') {
    acceptMod(element)
    if (document.getElementById('modal-laser').style.display == 'flex') {
      setTimeout(() => {
        document.getElementById('laser-output').focus();
      }, 100)

    }
  }
}


function QtyVerificationN(element) {
  let product = element.parentElement.parentElement.parentElement;
  let modInp = product.getElementsByClassName('mod-input-block')[0];
  if (modInp.style.display == 'none') {
    element.classList.toggle('active-btn'); 
    modInp.style.display = 'flex';
  } else if (modInp.style.display == 'flex') {
    modInp.style.display = 'none';
    element.classList.remove('active-btn'); 
  }
}


function getRecordData(product) {
  let productId = product.getElementsByClassName('product-id')[0].innerHTML;
  let barcode = product.getElementsByClassName('code-barre')[0].innerHTML;
  let name = product.getElementsByClassName('product-name')[0].innerHTML;
  let qty = product.getElementsByClassName('qty')[0].innerHTML.match(/(\d+)/)[0];
  let receivedQty = product.getElementsByClassName('received-qty')[0].innerHTML.match(/(\d+)/)[0];
  if (suffix.match('%26type%3Dpurchase')) {
    var pkgQty = product.getElementsByClassName('pkg-qty')[0].innerHTML.match(/(\d+)/)[0];
  } else {
    var pkgQty = '0';
  }

  let table = product.parentElement;
  let tableID = table.id;
  if (tableID == "scanned-laser-list") {
    // avoid indexing error due both scanned list composition dif
    // as laser scan is bind to one user, it is just a partial representation of scanned list
    // need to redirect towards full scanned list:
    table = document.getElementById('scanned-list');
  }


  let index;
  let tableElements = table.getElementsByClassName('product');
  for (var i = 0; i < tableElements.length; i++) {
    let id = tableElements[i].getElementsByClassName('product-id')[0].innerHTML;
    let ean = tableElements[i].getElementsByClassName('code-barre')[0].innerHTML;
    if ((id == productId & id != "0") | ean == barcode) {
      index = i;
    }
  }
  productData = {'name':name, 'id': productId, 'barcode':barcode,
                  'qty': qty, 'pckg_qty': pkgQty, 'qty_received': receivedQty,
                  'tableID':tableID, 'index': index}

  return productData
}


function correctTableID(tableID) {
  if (tableID == 'purchased-list') {
    tableID = 'dataframe entry_table';
  } else if (tableID == 'scanned-list') {
    tableID = 'dataframe queue_table';
  } else if (tableID == 'scanned-laser-list') {
    tableID = 'dataframe queue_table';
  } else if (tableID == 'verified-list') {
    tableID = 'dataframe done_table';
  }
  return tableID
}


function translateTableID(tableID) {
  if (tableID == 'dataframe entry_table') {
    tableID = 'purchased-list';
  } else if (tableID == 'dataframe queue_table') {
    tableID = 'scanned-list';
  } else if (tableID == 'dataframe done_table') {
    tableID = 'verified-list';
  }
  return tableID     
}

function get_suffix(url) {
  let array = url.split('%26type%3D');
  if (array.length > 1) {
    suffix = '%26type%3D' + array[array.length - 1];
    roomID = array[0].split('/')[array[0].split('/').length - 1];
  } else {
    suffix = roomID = url.split('/')[url.split('/').length - 1];
  }
  return roomID, suffix;
}

function get_state() {
  let state = 'open';
  for (const s of suffix.split('%26')) {
    if (s.split('%3D')[0] == 'state') {
      state = s.split('%3D')[1].split('?')[0];
    }
  }
  return state
}


function emptyPlaceholder(tableID) {
  console.log('get placeholder')
  let table = document.getElementById(tableID).parentNode;
  let productArray = table.getElementsByClassName('product');

  if (productArray.length == 0) {
    for (const msg of table.getElementsByClassName('situation')) {
      msg.innerHTML = 'Aucun produit';
    }
  } 
}

function removeEmptyPlaceholder(tableID) {
  let table = document.getElementById(tableID).parentNode;
  let placeholder = table.getElementsByClassName('situation')[0].innerHTML;

  if (placeholder != '') {
    table.getElementsByClassName('situation')[0].innerHTML = '';
  }
}


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


socket.on('move_product_to_queue', function(context) {
  //find product on entry table
  // append it to queue table
  
  let scannedEan = context.barcode
  let newItem = context.new_item
  let QueueTable = document.getElementById('scanned-list')
  let purchasedTable = document.getElementById('purchased-list');
  let colors = {'scanned': context.scanned_barcodes, 'new': context.new_items, 'mod': context.modified_items}

  if (roomID == context.room_id) {
    if (newItem) {
      // new item: add row in queue table
      CreateProductBubble(context, 'scanned-list', admin);
    } else {
      // search in entry table
      let productAray = purchasedTable.getElementsByClassName('product');
      for (const product of productAray) {
        let ean = product.getElementsByClassName('code-barre')[0].innerHTML;
        if (ean == scannedEan) {
          product.remove();
        }
      }
      CreateProductBubble(context, 'scanned-list', admin);
    }
  }
  doubleScanBlocker = false;
});

socket.on('modify_scanned_item', function(context) {
  //  open modal for scanner to modify product without living camera mode
  console.log('is in')
  let modal = document.getElementById('scanned-item-modal');
  console.log(context)

  CreateProductBubble(context, 'scanned-item-modal', admin)
  modal.style.display = 'flex';

});

socket.on('modify_scanned_laser_item', function(context) {
  //  open modal for scanner to modify product without living camera mode

  let modal = document.getElementById('scanned-item-modal-laser');
  CreateProductBubble(context, 'scanned-laser-list', admin)
  // CreateProductBubble(context, 'scanned-list', true)
  // modal.style.display = 'flex';
});














// CLOSING ACTION


function CloseCModal() {
  document.getElementById('confirmation-hub-modal').style.display = 'none';
  document.getElementById('html').style.overflowY = 'visible';
  document.getElementById('cancel-confirmation').hidden = false;
  document.getElementById('accept-confirmation').hidden = false;
  RemoveAutoVal()
}



const finisher = document.getElementById('closing-room');
finisher.onclick = function () {
  window.scrollTo(0, window.scrollY); 
  document.getElementById('confirmation-hub-modal').style.top = (window.scrollY - 5).toString() + 'px';
  document.getElementById('confirmation-hub-modal').style.display = 'flex';
  document.getElementById('html').style.overflowY = 'hidden';
  document.getElementById('heading-message').innerHTML = 'Fin de réception';
  document.getElementById('content-message').innerHTML = 'Veuillez confirmer la fin de réception.';

  document.getElementById('accept-confirmation').setAttribute('onclick','ClosingRoom()')
} 


function ClosingRoom() {
  context = {'roomID': roomID, 'suffix': suffix}
  CloseCModal()
  console.log('closing')
  socket.emit('finishing_room', context)
} 

socket.on('broacasted_finish', function(context) {
  if (roomID == context.roomID) {
    window.location = context.url
  }
});





suspender.onclick = function () {
  window.scrollTo(0, window.scrollY); 
  document.getElementById('confirmation-hub-modal').style.top = (window.scrollY - 5).toString() + 'px';
  document.getElementById('confirmation-hub-modal').style.display = 'flex';
  document.getElementById('html').style.overflowY = 'hidden';
  document.getElementById('heading-message').innerHTML = 'Suspendre la réception';
  document.getElementById('content-message').innerHTML = 'Veuillez confirmer la suspension de la réception.';

  document.getElementById('accept-confirmation').setAttribute('onclick','suspendingRoom()')
}


function suspendingRoom() {
  context = {'roomID': roomID, 'suffix': suffix}
  CloseCModal()
  console.log('suspending')
  socket.emit('suspending_room', context)
}

socket.on('broacasted_suspension', function(context) {
  if (roomID == context.roomID) {
    CloseCModal()
    window.location = context.url
  }
});


function autoValidation() {
  let container = document.getElementById('confirmation-container-content');
  
  let content = document.createElement('div');
  content.classList.add('auto-switch');

  let text = document.createElement('p');
  text.innerHTML = "Auto-validation:";


  let switcher = document.createElement('label');
  switcher.classList.add('switch');
  let inp = document.createElement('input');
  inp.setAttribute('type','checkbox');
  inp.classList.add('autoswitch');
  let sp = document.createElement('span');
  sp.classList.add('slider');
  sp.classList.add('round');
  switcher.appendChild(inp);
  switcher.appendChild(sp);

  content.appendChild(text);
  content.appendChild(switcher);

  container.appendChild(content);

  // deactivating for now
  document.getElementsByClassName('autoswitch')[0].disabled = true;
}

function RemoveAutoVal() {
  let container = document.getElementsByClassName('auto-switch')[0];
  if (container) {
    container.remove();
  }
}

verifier.onclick = function () {
  window.scrollTo(0, window.scrollY); 
  document.getElementById('confirmation-hub-modal').style.top = (window.scrollY - 5).toString() + 'px';
  document.getElementById('confirmation-hub-modal').style.display = 'flex';
  document.getElementById('html').style.overflowY = 'hidden';
  document.getElementById('heading-message').innerHTML = 'Validation de la réception';
  document.getElementById('content-message').innerHTML = "Confirmer l'envoie des données vers ODOO";
  autoValidation()

  document.getElementById('accept-confirmation').setAttribute('onclick','ValidatingRoom()')
}

function ValidatingRoom() {
  let autoval = document.getElementsByClassName('autoswitch')[0].checked;
  context = {'roomID': roomID, 'suffix': suffix, 'autoval': autoval}
  document.getElementById('content-message').innerHTML = "Envoie des données en cours...";
  document.getElementsByClassName('autoswitch')[0].disabled = true;
  document.getElementById('cancel-confirmation').hidden = true;
  document.getElementById('accept-confirmation').hidden = true;

  socket.emit('validation-purchase', context)
}

socket.on('close-room-on-validation', function(context) {
  if (roomID == context.roomID) {
    RemoveAutoVal();
    CloseCModal();
    window.location = context.url;
  }
});

socket.on('close-test-fail-error-window', function(context) {
  if (roomID == context.roomID) {
    let state = context.post_state;
    let test_name = state.failed;
    let item_list = state.string_list;

    RemoveAutoVal();
    document.getElementById('cancel-confirmation').hidden = false;
    document.getElementById('accept-confirmation').hidden = false;

    if (test_name  == 'odoo_exist') {
      document.getElementById('heading-message').innerHTML = 'Oups Odoo pose problème...';
      document.getElementById('content-message').innerHTML = "Produits inexistants sur odoo, ou erreur de code barre multiple: " + item_list;

    } else if (test_name == 'purchase_exist') {
      document.getElementById('heading-message').innerHTML = 'Commande: Produit inexistant';
      document.getElementById('content-message').innerHTML = "Veuillez rajouter les produits suivants dans la commande associée : " + item_list;
    } else if (test_name == 'validation_exist') {
      document.getElementById('heading-message').innerHTML = 'Commande déjà validée...';
      document.getElementById('content-message').innerHTML = "Il semble que la commande soit déjà validée. Vous n'avez rien a faire, le salon disparaitra lors de la prochaine mise à jour";
    }

    document.getElementById('accept-confirmation').setAttribute('onclick','CloseCModal()')
  }
});


recharger.onclick = function () {

  window.scrollTo(0, window.scrollY); 
  document.getElementById('confirmation-hub-modal').style.top = (window.scrollY - 5).toString() + 'px';
  document.getElementById('confirmation-hub-modal').style.display = 'flex';
  document.getElementById('html').style.overflowY = 'hidden';
  document.getElementById('heading-message').innerHTML = 'Rechargement des données';
  document.getElementById('content-message').innerHTML = "Veuillez confirmer le rechargement des données";

  document.getElementById('accept-confirmation').setAttribute('onclick','rechargingRoom()')
}

function rechargingRoom() {
  context = {'roomID': roomID, 'suffix': suffix}
  console.log('recharging')
  socket.emit('recharging_room', context)
  document.getElementById('content-message').innerHTML = "Chargement en cours...";
  document.getElementById('cancel-confirmation').hidden = true;
  document.getElementById('accept-confirmation').hidden = true;
}

socket.on('reload-on-recharge', function(context) {
  console.log('has recharged')
  CloseCModal()
  window.location.reload()
});

socket.on('broadcast-recharge', function(context) {
  if (roomID == context.roomID) {
    window.scrollTo(0, window.scrollY); 
    document.getElementById('confirmation-hub-modal').style.top = (window.scrollY - 5).toString() + 'px';
    document.getElementById('confirmation-hub-modal').style.display = 'flex';
    document.getElementById('html').style.overflowY = 'hidden';
    document.getElementById('heading-message').innerHTML = 'Rechargement des données';
    document.getElementById('content-message').innerHTML = "Des modifications ont été apportées depuis Odoo. Voulez vous recharger la page ?";

    document.getElementById('accept-confirmation').setAttribute('onclick','window.location.reload()')
  }
});


// del table ITEM

function UncheckBox(tableID) {
  let container = document.getElementById(tableID);
  let items = container.getElementsByClassName('product');

  for (const product of items) {
    let box = product.getElementsByClassName('check');
    if (box[0].checked) {
      box[0].checked = false;
    }
  }
}

function GenerateDelConfimartion(tableID) {
  if (admin) {
    let productArray = [];
    let nameArray = [];
    let container = document.getElementById(tableID);
    let items = container.getElementsByClassName('product');
  
    for (const product of items) {
      let box = product.getElementsByClassName('check');
      if (box[0].checked) {
        let productData = getRecordData(product)
        productArray.push(productData)
        nameArray.push(productData.name)
      }
    }
    window.scrollTo(0, window.scrollY); 
    document.getElementById('confirmation-hub-modal').style.top = (window.scrollY - 5).toString() + 'px';
    document.getElementById('confirmation-hub-modal').style.display = 'flex';
    document.getElementById('html').style.overflowY = 'hidden';
    document.getElementById('heading-message').innerHTML = 'Suppression de Produits';
    
    if (productArray.length == 0) {
      document.getElementById('content-message').innerHTML = "Veuillez selectionner des produits.";  
      document.getElementById('accept-confirmation').setAttribute('onclick',"CloseCModal()")
    } else {
      document.getElementById('content-message').innerHTML = "Voulez vous supprimer: <strong>" + nameArray.toString() + "</strong>";
      document.getElementById('accept-confirmation').setAttribute('onclick',"DelRequest('" + tableID + "')")
    }
  }
}

function DelRequest(tableID) {
  let index = [];
  let container = document.getElementById(tableID);
  let items = container.getElementsByClassName('product');

  for (const product of items) {
    let box = product.getElementsByClassName('check');
    if (box[0].checked) {
      let productData = getRecordData(product)
      index.push(productData.index)
    }
  }

  context = {'index': index, 'fromTable': tableID, 
              'roomID': roomID, 'suffix': suffix}
  console.log(context.index)

  socket.emit('del_item', context)
  CloseCModal()
  UncheckBox(tableID)
}

socket.on('broadcasted_deleted_item', function(context) {
  if (roomID == context.roomID) {
    let tableID = context.fromTable
    let index = context.index
    let container = document.getElementById(tableID)
    let items = container.getElementsByClassName('product');

    for (var i = index.length - 1; i >= 0; i--) {
      console.log(index[i])
      items[index[i]].remove()
    }
    updateRemainingProdcutToScan()
  }

});


// REDIRECTING ON DENIED ACCESS

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








// search verified item
function searchVerifiedItem(e) {
  if (e.key == 'Enter') {
    document.getElementById('search-product').blur()
  } else {
    let container = document.getElementById('verified-list');
    let search = document.getElementById('search-product').value.toLowerCase();
  
    if (search == '') {
      for (product of container.getElementsByClassName('product')) {
        product.hidden = false;
      }
  
    } else {
      for (product of container.getElementsByClassName('product')) {
        let name = product.getElementsByClassName('product-name')[0].innerHTML.toLowerCase();
        let barcode =  product.getElementsByClassName('code-barre')[0].innerHTML.toLowerCase();
  
        if (name.includes(search) || barcode.includes(search)) {
          product.hidden = false;
        } else {
          product.hidden = true;
        }
      } 
    }
  }
}

function resetVerifiedSearch() {
  document.getElementById('search-product').value = '';
  searchVerifiedItem({key: ''});
  document.getElementById('search-product').blur()
}


// stats block

function updateRemainingProdcutToScan() {
  let container = document.getElementById('purchased-list');
  let products = container.getElementsByClassName('product');
  document.getElementById('nb').innerHTML = '<strong>'+products.length.toString()+'</strong>';

  // var scale = 40;
  // const scaler = setInterval(() => {
  //   document.getElementById('nb').style.fontSize = scale.toString()+'px';
  //   console.log(scale)
  //   if (scale > 16) {
  //     scale -= 1;
  //   } else {
  //     document.getElementById('nb').style.fontSize = '16px';
  //     clearInterval(scaler)
  //   }
  // }, 10)
}