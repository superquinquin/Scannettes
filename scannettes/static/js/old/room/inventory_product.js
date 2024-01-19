


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

  // let pkgQTY = document.createElement('p');
  // pkgQTY.classList.add('pkg-qty');
  // pkgQTY.innerHTML = '<strong>NB Colis : </strong>' + context.pckg_qty;
  // qtyData.appendChild(pkgQTY);


  let QTY = document.createElement('p');
  QTY.classList.add('qty');
  QTY.innerHTML = '<strong>Quantité théorique : </strong>' + context.qty;
  QTY.setAttribute('style', 'margin-left: 0;');
  qtyData.appendChild(QTY);


  let receivedQTY = document.createElement('p');
  receivedQTY.classList.add('received-qty');
  if (tableID == 'verified-list') {
    receivedQTY.setAttribute('style', 'display: flex;');
  } else {
    receivedQTY.setAttribute('style', 'display: none;');
  }
  receivedQTY.innerHTML = '<strong>En stock : </strong> &#xA0 ' + context.qty_received;
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
    QTYQ.innerHTML = '<strong>La quantité théorique est-elle correct ?</strong>';
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
    labelInput.innerHTML = '<strong>Quantité en stock : </strong>';
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
