var config = {"colors": {"primary": "#fefa85", "secondary": "#3C312E", "ternary": "#FAEFEF", "new_items": "#FD8789", "new_items_if_exist": "#B5B3D0", "mod_items": "#FDC087", "normal_items": "#CFF2E8"}, "enable_video": true, "enable_audio": false, "ideal_width": 1920, "ideal_height": 1080, "ideal_mode": "environment", "frame_width": 300, "frame_height": 200, "fps": 120, "pkg_frequency": 2, "static_url": "/static", "secret_key": "xxxxxxx", "application_root": "/", "address": "http://localhost:5000", "host": "http://localhost", "port": "5000", "debug": false, "testing": false, "templates_auto_reload": true};
// INIT SOCKET & VARIABLES

const currentLoc = window.location.href;
const browser = get_browser_id();
const agent = get_agent();
const charged = isCharged();

var roomID, suffix = get_suffix(currentLoc);

var admin =  false;
const socket = io.connect(config.address);
const root = document.documentElement;
const adminClose = document.getElementById('admin-close');
const closing = document.getElementById('closing-room');
const aucdiv = document.getElementById('all-user-close');
const suspBlock = document.getElementById('suspension-block');
const verifBlock = document.getElementById('verif-block');
const suspender = document.getElementById('room-suspension');
const verifier = document.getElementById('admin-validation');
const finisher = document.getElementById('closing-room');
const delQueue = document.getElementById('del-from-queue');
const recharger = document.getElementById('room-recharge');

recharger.disabled = true;
verifBlock.hidden = true;
adminClose.hidden = true;
verifier.disabled = true
suspender.disabled = true;


// INIT 
////////////////////////////////////////////////////////////////////
root.style.setProperty('--primary', config.COLOR_PRIMARY);
root.style.setProperty('--secondary', config.COLOR_SECONDARY);
root.style.setProperty('--ternary', config.COLOR_TERNARY);

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

function get_agent() {
  let agent = "Unknown";
  const ua = {
    "Linux": /Linux/i,
    "Android": /Android/i,
    "BlackBerry": /BlackBerry/i,
    "Bluebird": /EF500/i,
    "Chrome OS": /CrOS/i,
    "Datalogic": /DL-AXIS/i,
    "Honeywell": /CT50/i,
    "iPad": /iPad/i,
    "iPhone": /iPhone/i,
    "iPod": /iPod/i,
    "macOS": /Macintosh/i,
    "Windows": /IEMobile|Windows/i,
    "Zebra": /TC70|TC55/i,
  }
  Object.keys(ua).map(v => navigator.userAgent.match(ua[v]) && (agent = v));
  return agent
}
//////////////////////////////////////////////////////////////////////


// ROOM SETUP RELATED TO ROOM STATUS (CLOSED, OPEN, DONE)
//////////////////////////////////////////////////////////////////////////////////////////////////////////
function admin_open_room_setup() {
  // used in granting permission event
  delQueue.hidden = false;
  adminClose.hidden = false;
  suspender.disabled = false;
  recharger.disabled = false;
}

function closed_room_setup() {
  // used in granting permission event
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
}

function done_room_setup() {
  // used in granting permission event
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

function isCharged() {
  var queue = document.getElementById('scanned-situation');
  var entries = document.getElementById('purchased-situation');
  var verified = document.getElementById('verified-situation');

  if (queue.innerHTML != "" && queue.innerHTML == entries.innerHTML && queue.innerHTML == verified.innerHTML) {
    return false
  } else {
    return true
  }
}
//////////////////////////////////////////////////////////////////////////////////////////////////////////



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
    scrolltopAfterElevate(product);
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


function searchVerifiedItem(e) {
  if (e.key == 'Enter') {
    document.getElementById('search-product').blur()
  } else {
    search_into_container(e, 'verified-list', 'search-verified-product')
  }
}

function searchPurchasedItem(e) {
  if (e.key == 'Enter') {
    document.getElementById('search-product').blur()
  } else {
    search_into_container(e, 'purchased-list', 'search-purchased-product')
  }
}

function search_into_container(e, c, inpfield) {
  let container = document.getElementById(c);
  let search = document.getElementById(inpfield).value.toLowerCase();
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

function resetSearch(list) {
  if (list == "purchased") {
    document.getElementById('search-purchased-product').value = '';
    searchPurchasedItem({key: ''});
    document.getElementById('search-purchased-product').blur();
  } else if (list == "verified") {
    document.getElementById('search-verified-product').value = '';
    searchVerifiedItem({key: ''});
    document.getElementById('search-verified-product').blur();
  }
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
  rescaleCModalContainer()
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

function rescaleCModalContainer(action) {
  let ch = document.getElementById('confirmation-container').clientHeight;
  let cw = document.getElementById('confirmation-container').clientWidth;
  let h = document.getElementById('confirmation-container').style.height;
  let w = document.getElementById('confirmation-container').style.width;
  // apply rescaling for computer screen on error modal
  if (action == "open" && ch == 250 && cw == 300) {
    document.getElementById('confirmation-container').style.height = "80%";
    document.getElementById('confirmation-container').style.width = "50%";
  } else if (action == "open" && h == "80%" && w == "50%") {
    document.getElementById('confirmation-container').style.height = "250px";
    document.getElementById('confirmation-container').style.width = "300px";
  } else if (action == "close") {
    document.getElementById('confirmation-container').style.height = "250px";
    document.getElementById('confirmation-container').style.width = "300px";
  }
}

function CloseCModal() {
  document.getElementById('confirmation-hub-modal').style.display = 'none';
  document.getElementById('html').style.overflowY = 'visible';
  document.getElementById('cancel-confirmation').hidden = false;
  document.getElementById('accept-confirmation').hidden = false;
  RemoveAutovalModule();
  rescaleCModalContainer("close")
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
        if (productData.name == "") {
          nameArray.push(productData.barcode)
        } else {
          nameArray.push(productData.name)
        }
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
        "Voulez vous supprimer: <strong>" + nameArray.toString().replace(',',', ') + "</strong>",
        "DelRequest('" + tableID + "')",
        false
      )
    }
  }
}

///////////////////////////////////////////////////////////////////////////////


function elevate(elm) {
  let product = elm.parentElement.parentElement.parentElement;
  let container = product.parentElement;
  let offset = 30;

  if (container.id == "scanned-laser-list" &&
    ["Linux", "macOS", "Windows", "Chrome OS"].includes(agent) == false) {
    let container = document.getElementById("scanned-laser-list");
    let containerTop = container.offsetTop;
    let containerScroll = container.scrollTop;
    let prodTop = product.offsetTop;
    let prodHeight = product.offsetHeight;
    let innerPos = prodTop - containerTop;
  } else if (container.id != "scanned-laser-list" &&
    ["Linux", "macOS", "Windows", "Chrome OS"].includes(agent) == false) {
    let currentTop = document.documentElement.scrollTop;
    let inner = window.innerHeight;
    let prodBot = product.getBoundingClientRect().bottom;
    window.scroll(0, currentTop - (inner - prodBot) + offset);
  }
}

function scrolltopAfterElevate(product) {
  let p = product;
//  if (product.parentElement.id=="scanned-laser-list" && 
//  ["Linux", "macOS", "Windows", "Chrome OS"].includes(agent) == false) {
//   scrolltop()
//  }
}


function closeLaser() {
  document.getElementById('modal-laser').style.display = "none";
  document.getElementById('html').style.overflowY = 'visible';
  modal_btn.disabled = false;
}


function CreateProductBubble(context, tableID, admin) {
  let container = document.getElementById(tableID);
  removeEmptyPlaceholder(tableID)

  let product = document.createElement('div');
  product.classList.add('product');
  if (context.new.length > 0 && context.new.includes(context.barcode) && context.name == "") {
    product.setAttribute('style','background-color:' + config.COLOR_NEW_ITEMS +';');
  } else if (context.mod.length > 0 && context.mod.includes(context.barcode)) {
    product.setAttribute('style','background-color:' + config.COLOR_MOD_ITEMS +';');
  } else if (context.new.length > 0 && context.new.includes(context.barcode) && context.name != "") {
    product.setAttribute('style','background-color:' + config.COLOR_NEW_ITEMS_IF_EXIST +';');
  } else {
    product.setAttribute('style','background-color:' + config.COLOR_NORMAL_ITEMS+ ';');
  }

  if (admin) {
    let box = document.createElement('input');
    box.setAttribute('type','checkbox');
    box.setAttribute('class','check');
    product.appendChild(box);
  }

  let name = document.createElement('p');
  name.classList.add('product-name');
  name.innerHTML = context.name;
  product.appendChild(name);

  let coreData = document.createElement('div');
  coreData.classList.add('core-data');

  let barCode = document.createElement('p');
  barCode.classList.add('code-barre');
  barCode.innerHTML = context.barcode;
  coreData.appendChild(barCode)

  let id = document.createElement('p')
  id.classList.add('product-id');
  id.setAttribute("hidden", "true");
  id.innerHTML = context.id;
  coreData.appendChild(id);

  product.appendChild(coreData);

  let qtyData = document.createElement('div');
  qtyData.classList.add('qty-data');

  let pkgQTY = document.createElement('p');
  pkgQTY.classList.add('pkg-qty');
  pkgQTY.innerHTML = '<strong>NB Colis : </strong>' + context.pckg_qty;
  qtyData.appendChild(pkgQTY);


  let QTY = document.createElement('p');
  QTY.classList.add('qty');
  QTY.innerHTML = '<strong>Quantité : </strong>' + context.qty;
  qtyData.appendChild(QTY);


  let receivedQTY = document.createElement('p');
  receivedQTY.classList.add('received-qty');
  if (tableID == 'verified-list') {
    receivedQTY.setAttribute('style', 'display: flex;');
  } else {
    receivedQTY.setAttribute('style', 'display: none;');
  }
  receivedQTY.innerHTML = '<strong>Reçue : </strong> &#xA0 ' + context.qty_received;
  qtyData.appendChild(receivedQTY);

  product.append(qtyData);

  if (get_state() != 'done') {
    let panel = document.createElement('div');
    panel.classList.add('panel');
  
    let questionName = document.createElement('div');
    questionName.classList.add('panel-question-name');
    if (tableID == 'verified-list') {
      questionName.setAttribute('style', 'display: none;');
    } else if (tableID == 'purchased-list' & admin){
      questionName.setAttribute('style', 'display: flex;');
    } else if (tableID == 'scanned-list') {
      questionName.setAttribute('style', 'display: flex;');
    } else if(tableID == 'scanned-item-modal') {
      questionName.setAttribute('style', 'display: flex;');
    } else if (tableID == 'scanned-laser-list') {
      questionName.setAttribute('style', 'display: flex;');
    } else {
      questionName.setAttribute('style', 'display: none;');
    }
    
    
    let nameQ = document.createElement('p');
    nameQ.innerHTML = '<strong>Est-ce le bon produit ?</strong>';
    questionName.appendChild(nameQ);
  
    let nameYBtn = document.createElement('button');
    nameYBtn.classList.add('panel-btn');
    nameYBtn.setAttribute('onclick',"NameVerificationY(this)");
    nameYBtn.innerHTML = 'Oui'
    questionName.appendChild(nameYBtn);
  
    let nameNBtn = document.createElement('button');
    nameNBtn.classList.add('panel-btn');
    nameNBtn.setAttribute('onclick',"WrongProductConfirmation(this)");
    nameNBtn.innerHTML = 'Non'
    questionName.appendChild(nameNBtn);
  
    // panel.appendChild(questionName);
  
  
    let questionQTY = document.createElement('div');
    questionQTY.classList.add('panel-question-qty');
    /////// if NOT QUESTION NAME
    if (tableID == 'verified-list') {
      questionQTY.setAttribute('style', 'display: flex;');
    } else if (tableID == 'purchased-list' & admin){
      questionQTY.setAttribute('style', 'display: flex;');
    } else if (tableID == 'scanned-list') {
      questionQTY.setAttribute('style', 'display: flex;');
    } else if(tableID == 'scanned-item-modal') {
      questionQTY.setAttribute('style', 'display: flex;');
    } else if (tableID == 'scanned-laser-list') {
      questionQTY.setAttribute('style', 'display: flex;');
    } else {
      questionQTY.setAttribute('style', 'display: none;');
    }

    /////// IF QUESTION NAME
    // if (tableID == 'verified-list') {
    //   questionQTY.setAttribute('style', 'display: flex;');
    // } else {
    //   questionQTY.setAttribute('style', 'display: none;');
    // }
    
    let QTYQ = document.createElement('p');
    QTYQ.innerHTML = '<strong>La quantité reçue est-elle correcte ?</strong>';
    questionQTY.appendChild(QTYQ);
    
    let QTYYBtn = document.createElement('button');
    QTYYBtn.classList.add('panel-btn');
    QTYYBtn.setAttribute('onclick',"QtyVerificationY(this)");
    if (tableID == 'verified-list') {QTYYBtn.setAttribute('style','visibility: hidden')};
    QTYYBtn.innerHTML = 'Oui';
    questionQTY.appendChild(QTYYBtn);
  
    let QTYNBtn = document.createElement('button');
    QTYNBtn.classList.add('panel-btn');
    QTYNBtn.setAttribute('onclick',"QtyVerificationN(this)");
    QTYNBtn.innerHTML = 'Modifier';
    questionQTY.appendChild(QTYNBtn);
    panel.appendChild(questionQTY);
    product.appendChild(panel);
  
  
  
    let inputMod = document.createElement('div');
    inputMod.classList.add('mod-input-block');
    inputMod.setAttribute('style', 'display: none;');
  
    let inpBlock = document.createElement('div');
    inpBlock.classList.add('input-block');
  
    let labelInput = document.createElement('label');
    labelInput.setAttribute('for', 'mod-input');
    labelInput.innerHTML = '<strong>Nouvelle quantité reçue : </strong>';
    inpBlock.appendChild(labelInput);
  
    let inp = document.createElement('input');
    inp.classList.add('mod-input');
    inp.setAttribute('type', 'number');
    inp.setAttribute('onclick', 'elevate(this)');
    inp.setAttribute('onkeydown', 'acceptModFromKey(this)')
    inpBlock.appendChild(inp);
    inputMod.appendChild(inpBlock)
  
    let modBtn = document.createElement('div');
    modBtn.classList.add('mod-btn');
  
    let modAcceptBtn = document.createElement('button');
    modAcceptBtn.classList.add('modAccept');
    modAcceptBtn.setAttribute('onclick',"acceptMod(this)");
    modAcceptBtn.innerHTML = 'Confirmer';
    modBtn.appendChild(modAcceptBtn)
  
    inputMod.appendChild(modBtn)
  
    product.append(inputMod)
  }

  container.appendChild(product)
}


const FPS = config.CAMERA_FPS;
const CPF = config.CAMERA_PKG_FREQUENCY
const croppedWidth = config.CAMERA_FRAME_WIDTH;
const croppedHeight = config.CAMERA_FRAME_HEIGHT;

var streaming = false;

const modal_btn = document.getElementById("display_modal");
const modal = document.getElementById("modal");
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d', { alpha: false });

const croppedCanvas = document.getElementById('cropped-canvas');
const croppedCTX = croppedCanvas.getContext('2d', { alpha: false });
croppedCTX.canvas.hidden = true;

// MODAL LASER
const modal_laser_btn = document.getElementById('display_laser');
const modal_laser = document.getElementById('modal-laser');
const laserOutput = document.getElementById('laser-output');


// CAMERA SCANNER MODAL APPLICATION
modal_btn.onclick = async function (e) {
  display = modal.style.display;
  if(!display | display == 'none'){
    var streamingEvent = e;
    console.log('oppening modal & start streaming')

    modal.style.display = 'flex';
    document.getElementById('html').style.overflowY = 'hidden';
    modal_laser_btn.disabled = true;

    streaming = true;
    video = document.querySelector("#videoElement");

    if (navigator.mediaDevices.getUserMedia) {
      var stream = await navigator.mediaDevices.getUserMedia({ video:      config.CAMERA_ENABLE_VIDEO,
                                                               audio:      config.CAMERA_ENABLE_AUDIO, 
                                                               width:      { ideal: config.CAMERA_IDEAL_WIDTH }, 
                                                               height:     { ideal: config.CAMERA_IDEAL_HEIGHT },
                                                               facingMode: { exact: config.CAMERA_IDEAL_MODE }
                                                              })
      video.srcObject = stream;
      WIDTH = stream.getVideoTracks()[0].getSettings().width;
      HEIGHT = stream.getVideoTracks()[0].getSettings().height;
    } 
    

    canvas.width = video.width = WIDTH;
    canvas.height = video.height = HEIGHT;
    croppedCanvas.width = croppedWidth;
    croppedCanvas.height = croppedHeight;
    ctx.lineWidth = 3;
    ctx.strokeStyle = "blue";
    var cropX = Math.trunc(Math.abs(video.width - croppedWidth) / 2);
    var cropY = Math.trunc(Math.abs(video.height - croppedHeight) / 2);
    let frame_counter = 0;
    let color_counter = 0;

    setInterval(() => {
      if(streaming) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        if (ctx.strokeStyle === '#1df700' && color_counter < 16) {
          color_counter += 1;
        } else if (ctx.strokeStyle === '#1df700' && color_counter == 16) {
          ctx.strokeStyle = "blue";
          color_counter = 0;
        }

        draw_corner(cropX, cropY, 40, 'topleft');
        draw_corner(cropX, cropY + croppedHeight, 40, 'bottomleft');
        draw_corner(cropX + croppedWidth, cropY, 40, 'topright');
        draw_corner(cropX + croppedWidth, cropY + croppedHeight, 40, 'bottomright');

        croppedCTX.drawImage(video,cropX, cropY, croppedWidth, croppedHeight, 0, 0, croppedWidth, croppedHeight);

        if(frame_counter == CPF) {

          let pixels = croppedCTX.getImageData(0, 0, croppedWidth, croppedHeight).data;
          let grayscaleArray = [];
          for (var i = 0; i < pixels.length; i += 4) {
            let pixelIntensity = parseInt((pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3);
            grayscaleArray.push(pixelIntensity)
          }
          var B64Image = btoa(String.fromCharCode.apply(null, new Uint8Array(grayscaleArray)));
          var data = {'image': B64Image, 'id': roomID};
          socket.emit('image', data);
          frame_counter = 0;
        } else {
          frame_counter += 1;
        }
      } else {
        clearInterval();
      }
    }, 10000/FPS);

  }else {
    console.log('closing modal & stop streaming');
    modal.style.display = 'none';
    document.getElementById('html').style.overflowY = 'visible';
    modal_laser_btn.disabled = false;
    stopStreamedVideo(video);
    streaming = false;
  }
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


function stopStreamedVideo(videoElem) {
  var stream = videoElem.srcObject;
  var tracks = stream.getTracks();

  tracks.forEach(function(track) {
    track.stop();
  });

  videoElem.srcObject = null;
}


socket.on('change_color', function() {
  ctx.strokeStyle = "#1df700";
});




/////////////////////////////////////////// LASER SCANNER
var doubleScanBlocker = false;
var lastScanned = '';

modal_laser_btn.onclick =  function () {
  if (modal_laser.style.display != 'flex') {
    modal_laser.style.display = 'flex';
    document.getElementById('html').style.overflowY = 'hidden';
    modal_btn.disabled = true;
    laserOutput.value = "";
    laserOutput.focus()

    if (modal_laser.style.display == 'flex') {
      document.getElementsByTagName("body")[0].addEventListener("click", keepLaserFocus);
    }

  } else {
    modal_laser.style.display = 'none';
    document.getElementById('html').style.overflowY = 'visible';
    modal_btn.disabled = false;
  }
}


window.addEventListener("keydown", function (e) {
  if (document.activeElement === laserOutput) {
    if (e.key != 'Shift' & e.key != 'Enter' & /^-?\d+$/.test(e.key)) {
      if (document.activeElement === laserOutput) {
        // tricks to make sure not writing ean number wwhile modifying qty
        laserOutput.value += e.key
        laserOutputAutoClearance()
      }
    }
  }
});

// SENDING SCANNER OUTPUT
laserOutput.addEventListener('keypress', function(e) {
  if (e.key === 'Enter' 
      && document.activeElement === laserOutput) {
    
    let barcode = laserOutput.value;
    let barcodeLength = barcode.length;
    let isnan = isNaN(Number(barcode));
    let data = {'barcode': barcode, 'id': roomID};

    if ((barcodeLength == 13 || barcodeLength == 8)
         && isnan == false) {
      if (barcode != lastScanned) {
        if (barcode != '') {
          socket.emit('laser', data);
          lastScanned = barcode;
        }
      }

    } else {
      let errorBox = document.getElementById('errorBox');
      let errorText = document.getElementById('errorText');
      errorBox.style.border = "solid 3px red";
      errorText.innerHTML = `<strong>Erreur: Réponse anormale du scanner</strong>
                              <br>Si de nouvelles erreurs apparaissent : 
                              <br><strong>débranchez et rebranchez le scanner à l'appareil</strong>,
                              <br><strong>Ou rechargez la page</strong>,
                              <br>Ou cherchez l'aide d'un.e employé.e`;
      setTimeout(() => {
        errorBox.style.border = "0";
        errorText.innerHTML = "";
      }, 1500);                       
    }
    laserOutput.value = "";
  }
});


function keepLaserFocus() {
  if (modal_laser.style.display == 'flex') {
    console.log('auto focus')
    if (laserOutput === document.activeElement) {
      var pass;
    } else if ((document.activeElement.className.match('mod-input'))){
      var pass;
    } else {
      laserOutput.focus()
    }
  }
}


function laserOutputAutoClearance() {
  let len = laserOutput.length
  setTimeout(() => {
    let newLen = laserOutput.length

    if (newLen == len) {
      laserOutput.value = "";
    }
  }, 1000); 
}


socket.on('already-scanned-alert', function(context) {
  let errorBox = document.getElementById('errorBox');
  let errorText = document.getElementById('errorText');
  errorBox.style.border = "solid 3px red";
  errorText.innerHTML = `<strong>Produit déjà scanné!</strong>`;
  setTimeout(() => {
    errorBox.style.border = "0";
    errorText.innerHTML = "";
  }, 3000);
});
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
