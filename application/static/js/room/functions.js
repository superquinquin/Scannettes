//CONTAINS MOST FUNCTIONS FOR THE ROOM TO RUN PROPERLY
//CONTAINS ALL THE EXCLUSIVE FUNCTIONS FOR ROOM OTHER THAN INIT FUNCTIONS AND CAMERA AND PRODUCT ELEMENT FUNCTIONS
// FOR OTHERS FUNCTIONS REFERS TO: init.js, global_functions.js.




// PRODUCT BUBLE MODULARITY UNDER USER ACTIONS
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
function NameVerificationY(element) {
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

function QtyVerificationY(element) {

  let product = element.parentElement.parentElement.parentElement;
  let productData = getRecordData(product);

  let tableID = correctTableID(productData.tableID);
  context = {'roomID': roomID,
              'table': tableID,
              'index': productData.index,
              'newqty': null,
              'barcode': productData.barcode, 
              'product_id': productData.id,
              'type': 'val'};

  socket.emit('update_table', context);
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
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////


// UTILS FUNCTIONS FOR TABLES
///////////////////////////////////////////////////////////////
function correctTableID(tableID) {
  if (tableID == 'purchased-list') {
    tableID = 'table_entries';
  } else if (tableID == 'scanned-list') {
    tableID = 'table_queue';
  } else if (tableID == 'scanned-laser-list') {
    tableID = 'table_queue';
  } else if (tableID == 'verified-list') {
    tableID = 'table_done';
  }
  return tableID
}


function translateTableID(tableID) {
  if (tableID == 'table_entries') {
    tableID = 'purchased-list';
  } else if (tableID == 'table_queue') {
    tableID = 'scanned-list';
  } else if (tableID == 'table_done') {
    tableID = 'verified-list';
  }
  return tableID     
}

function getRecordData(product) {
  let table = product.parentElement;
  let tableID = table.id;
  let productId = product.getElementsByClassName('product-id')[0].innerHTML;
  let barcode = product.getElementsByClassName('code-barre')[0].innerHTML;
  let name = product.getElementsByClassName('product-name')[0].innerHTML;
  let qty = product.getElementsByClassName('qty')[0].innerHTML.match(/(\d+)/)[0];
  let receivedQty = product.getElementsByClassName('received-qty')[0].innerHTML.match(/(\d+)/)[0];
  let pkgQty = '0';
  if (suffix.match('%26type%3Dpurchase')) {
    pkgQty = product.getElementsByClassName('pkg-qty')[0].innerHTML.match(/(\d+)/)[0];
  }

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

  return {'name':name, 'id': productId, 'barcode':barcode,
          'qty': qty, 'pckg_qty': pkgQty, 'qty_received': receivedQty,
          'tableID':tableID, 'index': index}
}

function acceptMod(element) {
  //mod items 
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
    fadingRedFieldOnError(input);
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

function emptyPlaceholder(tableID) {
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

function fill_table(target, context, content, is_admin) {
  // used in loading room event
  emptyPlaceholder(target);
  for (const product of content) {
    product.scanned = context.scanned;
    product.new = context.new;
    product.mod = context.mod;
    CreateProductBubble(product, target, is_admin);
  }
}

function removeFromTableWithEan(table, barcode) {
  let productAray = table.getElementsByClassName('product');
  for (const product of productAray) {
    let ean = product.getElementsByClassName('code-barre')[0].innerHTML;
    if (ean == barcode) {
      product.remove();
    }
  }
}

function DelRequest(tableID) {
  let index = [];
  let container = document.getElementById(tableID);
  let items = container.getElementsByClassName('product');
  tableID = correctTableID(tableID);

  for (const product of items) {
    let box = product.getElementsByClassName('check');
    if (box[0].checked) {
      let productData = getRecordData(product)
      index.push(productData.index)
    }
  }

  context = {'index': index, 'fromTable': tableID, 
              'roomID': roomID, 'suffix': suffix}

  socket.emit('del_item', context)
  CloseCModal()
  UncheckBox(tableID)
}

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

///////////////
//////////////////////////////////////////////////////////////////////////

// SEARCH VERIFIED ITEM BAR
////////////////////////////////////////////////////////////////////////////////////////
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
//////////////////////////////////////////////////////////////////////////////////////////////////////

// STATS
///////////////////////////////////////////////////////////////////////////////////////////////
function updateRemainingProdcutToScan() {
  let container = document.getElementById('purchased-list');
  let products = container.getElementsByClassName('product');
  document.getElementById('nb').innerHTML = '<strong>'+products.length.toString()+'</strong>';
}
/////////////////////////////////////////////////////////////////////////////////////////////////

// MODAL FUNCTIONS
///////////////////////////////////////////////////////////////////////////////
function openCModal(headerMsg, bodyMsg, closeFunc, autoVal) {
  window.scrollTo(0, window.scrollY); 
  document.getElementById('confirmation-hub-modal').style.top = (window.scrollY - 5).toString() + 'px';
  document.getElementById('confirmation-hub-modal').style.display = 'flex';
  document.getElementById('html').style.overflowY = 'hidden';
  document.getElementById('heading-message').innerHTML = headerMsg;
  document.getElementById('content-message').innerHTML = bodyMsg;
  if (autoVal) {
    autoValidationModule();
  }
  document.getElementById('accept-confirmation').setAttribute('onclick', closeFunc);
}

function autoValidationModule() {
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

function RemoveAutovalModule() {
  let container = document.getElementsByClassName('auto-switch')[0];
  if (container) {
    container.remove();
  }
}

function CloseCModal() {
  document.getElementById('confirmation-hub-modal').style.display = 'none';
  document.getElementById('html').style.overflowY = 'visible';
  document.getElementById('cancel-confirmation').hidden = false;
  document.getElementById('accept-confirmation').hidden = false;
  RemoveAutovalModule();
}

function emitCEvent(event) {
  let autoval = false;
  if (event == 'validation-purchase') {
    autoval = document.getElementsByClassName('autoswitch')[0].checked;
  }
  context = {'roomID': roomID, 'suffix': suffix, 'autoval': autoval};
  socket.emit(event, context);
}

function emitProcess(bodyMsg) {
  document.getElementById('content-message').innerHTML = bodyMsg;
  document.getElementsByClassName('autoswitch')[0].disabled = true;
  document.getElementById('cancel-confirmation').hidden = true;
  document.getElementById('accept-confirmation').hidden = true;
}

function ClosingRoom() {
  emitCEvent('finishing_room');
  CloseCModal();
} 

function suspendingRoom() {
  emitCEvent('suspending_room');
  CloseCModal();
}

function rechargingRoom() {
  emitCEvent('recharging_room');
  emitProcess("Chargement en cours...");
}

function nullification() {
  emitCEvent('nullification');
  emitProcess("Processus en cours...");
}

function ValidatingRoom() {
  emitProcess("Envoie des données en cours...");
  emitCEvent('validation-purchase');
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

    if (productArray.length == 0) {
      openCModal('Suppression de Produits',
        "Veuillez selectionner des produits.",
        "CloseCModal()",
        false
      )

    } else {
      openCModal('Suppression de Produits',
        "Voulez vous supprimer: <strong>" + nameArray.toString() + "</strong>",
        "DelRequest('" + tableID + "')",
        false
      )
    }
  }
}

///////////////////////////////////////////////////////////////////////////////








