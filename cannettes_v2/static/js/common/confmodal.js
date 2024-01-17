

function openCModal(headerMsg, bodyMsg, closeFunc, openContent="") {
    const page = document.getElementById('html');
    const modal = document.getElementById("confirmation-modal");
    const header = document.getElementById('heading-message');
    const message = document.getElementById('content-message');
    const content = document.getElementById('open-content');
    const button = document.getElementById('accept-confirmation');

    centerModal(modal);
    lockwindow();

    modal.style.display = 'flex';
    header.innerHTML = headerMsg;
    message.innerHTML = bodyMsg;
    if (openContent != "") {
        content.appendChild(openContent);
    }
    button.setAttribute('onclick', closeFunc);
}

function CloseCModal() {
    lockwindow();
    document.getElementById('open-content').innerHTML = "";
    document.getElementById('confirmation-modal').style.display = 'none';
    document.getElementById('cancel-confirmation').hidden = false;
    document.getElementById('accept-confirmation').hidden = false;
}


function centerModal(modal) {
    modal.style.top = (window.scrollY - 5).toString() + 'px';
}

function lockwindow() {
    let html = document.getElementsByTagName("html")[0];
    let yflow = html.style.overflowY;
    if (yflow === 'visible' || yflow === "") {
        html.style.overflowY = 'hidden';
    } else {
        html.style.overflowY = 'visible';
    }
}

function lockConfModal() {
    const accept = document.getElementById('accept-confirmation');
    const cancel = document.getElementById('cancel-confirmation');
    if (accept.hidden === true) {
        accept.hidden = false;
        cancel.hidden = false;
    } else {
        accept.hidden = true;
        cancel.hidden = true;
    }
}

function formatListing(strings) {
    let ul = document.createElement("ul");
    for (str of strings) {
        let li = document.createElement("li");
        li.innerText = str;
        ul.appendChild(li);
    }
    return ul;
}