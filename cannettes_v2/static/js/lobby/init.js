// INIT SOCKET AND VARIABLE FOR LOBBY.

const currentLoc = window.location.href;
var suffix = get_suffix(currentLoc);
var browser = get_browser_id();
var charged = false;

const socket = io.connect(config.address);
//MAIN
const root = document.documentElement;
const ptype = document.getElementById('pType-check');

const room_list = document.getElementById('room-listing');
const room_to_verify_list = document.getElementById('room-verify-listing');
const room_historic = document.getElementById('room-historic');


//Modal
const roomName = document.getElementById('room-name');
const roomPassword = document.getElementById('room-password');
const purchase = document.getElementById('purchases');
const inventory = document.getElementById('rayons');
const creationModal = document.getElementById('creation-modal');

const createRoom = document.getElementById('createRoom');
const CancelCreationRoom = document.getElementById('CancelRoom');
//QRCODE
const qCodeBtn = document.getElementById('qrcode-btn');

// INIT FUNCTION
root.style.setProperty('--primary', config.colors.primary);
root.style.setProperty('--secondary', config.colors.secondary);
root.style.setProperty('--ternary', config.colors.ternary);

function get_suffix(url) {
    let array = url.split('%26id%3D');
    if (array.length > 1) {
      suffix = '%26id%3D' + array[array.length - 1];
    } else {
      suffix = url.split('/')[url.split('/').length - 1];
    }
    return suffix;
}