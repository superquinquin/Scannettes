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