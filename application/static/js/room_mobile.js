
    var browser = get_browser_id()
    var roomID;
    var suffix;
    var admin =  false;
    const currentLoc = window.location.href;
    roomID, suffix = get_suffix(currentLoc)

    const socket = io.connect(config.ADDRESS);

    const adminClose = document.getElementById('admin-close');
    const suspender = document.getElementById('room-suspension');
    const verifier = document.getElementById('admin-validation');
    const recharger = document.getElementById('room-recharge');
    adminClose.hidden = true;
    verifier.disabled = true;
    recharger.disabled = true;
    suspender.disabled = true;

    const delQueue = document.getElementById('del-from-queue');
    const unlockQueue = document.getElementById('unlock-from-queue');
    
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
      socket.emit('verify_connection', {'suffix': suffix, 'browser_id': browser})
    });

    socket.on('load_existing_room', function(context) {
      //header
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
    });


    socket.on('grant_permission', () => {
      console.log('grant permission')
      admin = true;
      delQueue.hidden = false;
      adminClose.hidden = false;
      suspender.disabled = false;
      verifier.disabled = false;
      recharger.disabled = false;
      socket.emit('join_room', roomID);
    });

    socket.on('denied_permission', () => {
      socket.emit('join_room', roomID);
    });








    const collapser = document.getElementsByClassName("collaps-block");

    for (var i = 0; i < collapser.length; i++) {
      collapser[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        var delBtn = content.nextElementSibling;
        var unlockBtn = delBtn.nextElementSibling;
        if (content.style.display == 'flex'){
          content.style.display = 'none';
          if (admin) {
            delBtn.hidden = true;
            unlockBtn.hidden = true;
          }

        } else {
          content.style.display = 'flex';
          if (admin) {
            delBtn.hidden = false;
            unlockBtn.hidden = false;
          }
        } 
      });
    }

    function CreateProductBubble(context, tableID, admin) {

      let container = document.getElementById(tableID);
      removeEmptyPlaceholder(tableID)

      let product = document.createElement('div');
      product.classList.add('product');
      if (context.new.length > 0 & context.new.includes(context.barcode)) {
        product.setAttribute('style','background-color: #ff7866;')
      } else if (context.mod.length > 0 & context.mod.includes(context.barcode)) {
        product.setAttribute('style','background-color: #ff9f40;')
      } else {
        product.setAttribute('style','background-color: #fffee8;')
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

      let QTY = document.createElement('p');
      QTY.classList.add('qty');
      QTY.innerHTML = '<strong>Quantité : </strong>' + context.qty;
      qtyData.appendChild(QTY);

      let pkgQTY = document.createElement('p');
      pkgQTY.classList.add('pkg-qty');
      pkgQTY.innerHTML = '<strong>NB Colis : </strong>' + context.pckg_qty;
      qtyData.appendChild(pkgQTY);

      let receivedQTY = document.createElement('p');
      receivedQTY.classList.add('received-qty');
      if (tableID == 'verified-list') {
        receivedQTY.setAttribute('style', 'display: flex;');
      } else {
        receivedQTY.setAttribute('style', 'display: none;');
      }
      receivedQTY.innerHTML = '<strong>Reçue : </strong>' + context.qty_received;
      qtyData.appendChild(receivedQTY);

      product.append(qtyData);

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

      panel.appendChild(questionName);


      let questionQTY = document.createElement('div');
      questionQTY.classList.add('panel-question-qty');
      if (tableID == 'verified-list') {
        questionQTY.setAttribute('style', 'display: flex;');
      } else {
        questionQTY.setAttribute('style', 'display: none;');
      }
      
      let QTYQ = document.createElement('p');
      QTYQ.innerHTML = '<strong>La quantitée reçue est-elle correct ?</strong>';
      questionQTY.appendChild(QTYQ);

      let QTYYBtn = document.createElement('button');
      QTYYBtn.classList.add('panel-btn');
      QTYYBtn.setAttribute('onclick',"QtyVerificationY(this)");
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
      labelInput.innerHTML = '<strong>Quantité reçue : </strong>';
      inpBlock.appendChild(labelInput);

      let inp = document.createElement('input');
      inp.classList.add('mod-input');
      inp.setAttribute('type', 'text');
      inpBlock.appendChild(inp);
      inputMod.appendChild(inpBlock)

      let modBtn = document.createElement('div');
      modBtn.classList.add('mod-btn');
    
      let modAcceptBtn = document.createElement('button');
      modAcceptBtn.classList.add('modAccept');
      modAcceptBtn.setAttribute('onclick',"acceptMod(this)");
      modAcceptBtn.innerHTML = 'Confirmer';
      modBtn.appendChild(modAcceptBtn)

      // let modCancelBtn = document.createElement('button');
      // modCancelBtn.classList.add('modCancel');
      // modCancelBtn.innerHTML = 'Annuler';
      // modBtn.appendChild(modCancelBtn)
      inputMod.appendChild(modBtn)

      product.append(inputMod)
      container.appendChild(product)
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
        let receiver = product.getElementsByClassName('received-qty');

         
        if (type == 'mod') {
          let newQty = context.newqty;
          receiver.innerHTML = '<strong>Reçue : <\strong> ' + newQty;
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
        }
      }
    });

    function RemoveFromScannerContainer(tableID, barcode, productId) {
      let container = document.getElementById(tableID);
      for (const product of container.getElementsByClassName('product')) {
        let id = product.getElementsByClassName('product-id')[0].innerHTML;
        let ean = product.getElementsByClassName('code-barre')[0].innerHTML;

        if ((id == productId & id != "0") | ean == barcode) {
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



    function QtyVerificationN(element) {
      let product = element.parentElement.parentElement.parentElement;
      let modInp = product.getElementsByClassName('mod-input-block')[0];
      if (modInp.style.display == 'none') {
        modInp.style.display = 'flex';
      } else if (modInp.style.display == 'flex') {
        modInp.style.display = 'none';
      }
    }


    function getRecordData(product) {
      let productId = product.getElementsByClassName('product-id')[0].innerHTML;
      let barcode = product.getElementsByClassName('code-barre')[0].innerHTML;
      let name = product.getElementsByClassName('product-name')[0].innerHTML;
      let qty = product.getElementsByClassName('qty')[0].innerHTML.match(/(\d+)/)[0];
      let pkgQty = product.getElementsByClassName('pkg-qty')[0].innerHTML.match(/(\d+)/)[0];
      let receivedQty = product.getElementsByClassName('received-qty')[0].innerHTML.match(/(\d+)/)[0];

      let table = product.parentElement;
      let tableID = table.id;
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
      let array = url.split('%26id%3D');
      if (array.length > 1) {
        suffix = '%26id%3D' + array[array.length - 1];
        roomID = array[0].split('/')[array[0].split('/').length - 1];
      } else {
        suffix = roomID = url.split('/')[url.split('/').length - 1];
      }
      return roomID, suffix;
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
      bubble.style.left = (width / 2 - 150).toString() + 'px';

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
    }

    

    const finisher = document.getElementById('closing-room');
    finisher.onclick = function () {
      window.scrollTo(0,0); 
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
      window.scrollTo(0,0); 
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




    verifier.onclick = function () {
      window.scrollTo(0,0); 
      document.getElementById('confirmation-hub-modal').style.display = 'flex';
      document.getElementById('html').style.overflowY = 'hidden';
      document.getElementById('heading-message').innerHTML = 'Validation de la réception';
      document.getElementById('content-message').innerHTML = "Confirmer l'envoie des données vers ODOO";

      document.getElementById('accept-confirmation').setAttribute('onclick','ValidatingRoom()')
    }

    function ValidatingRoom() {
      context = {'roomID': roomID, 'suffix': suffix}
      console.log('Validation')
      CloseCModal()

      socket.emit('validation-purchase', context)
    }

    socket.on('close-room-on-validation', function(context) {
      if (roomID == context.roomID) {
        CloseCModal()
        window.location = context.url
      }
    });

    socket.on('close-test-fail-error-window', function(context) {
      if (roomID == context.roomID) {
        let state = context.post_state
        let test_name = state.failed
        let item_list = state.string_list

        window.scrollTo(0,0); 
        document.getElementById('confirmation-hub-modal').style.display = 'flex';
        document.getElementById('html').style.overflowY = 'hidden';

        if (test_name  == 'odoo_exist') {
          document.getElementById('heading-message').innerHTML = 'Odoo: Produit inexistant';
          document.getElementById('content-message').innerHTML = "Veuillez rajouter les produits suivants dans Odoo, puis dans la commande associée: " + item_list;

        } else if (test_name == 'purchase_exist') {
          document.getElementById('heading-message').innerHTML = 'Commande: Produit inexistant';
          document.getElementById('content-message').innerHTML = "Veuillez rajouter les produits suivants dans la commande associée : " + item_list;
        }
        document.getElementById('accept-confirmation').setAttribute('onclick','CloseCModal()')
      }
    });


    recharger.onclick = function () {
      window.scrollTo(0,0); 
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
    }

    socket.on('reload-on-recharge', function(context) {
      console.log('has recharged')
      CloseCModal()
      window.location.reload()
    });

    socket.on('broadcast-recharge', function(context) {
      if (roomID == context.roomID) {
        window.scrollTo(0,0); 
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
      window.scrollTo(0,0); 
      document.getElementById('confirmation-hub-modal').style.display = 'flex';
      document.getElementById('html').style.overflowY = 'hidden';
      document.getElementById('heading-message').innerHTML = 'Suppression de Produits';
      document.getElementById('content-message').innerHTML = "Voulez vous supprimer: <strong>" + nameArray.toString() + "</strong>";

      document.getElementById('accept-confirmation').setAttribute('onclick',"DelRequest('" + tableID + "')")
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
      }
    });