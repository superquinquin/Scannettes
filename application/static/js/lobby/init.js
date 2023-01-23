// INIT SOCKET AND VARIABLE FOR LOBBY.

const currentLoc = window.location.href;
var suffix = get_suffix(currentLoc);
var browser = get_browser_id();
var charged = false;

const socket = io.connect(config.ADDRESS);
//MAIN
const roomManagement = document.getElementById('room-management');
const roomAssembler = document.getElementById('room-assembler');
const create_btn = document.getElementById('create-btn');
const del_btn = document.getElementById('del-btn');
const reset_btn = document.getElementById('reset-btn');
const asmbl_btn = document.getElementById('asmbl-btn');
const room_list = document.getElementById('room-listing');
const room_to_verify_list = document.getElementById('room-verify-listing');
const room_historic = document.getElementById('room-historic');
const verifySection = document.getElementById('room-to-verify');
const historicSection = document.getElementById('historic');
const checkAll = document.getElementById('checkAll');
//Modal
const roomName = document.getElementById('room-name');
const roomPassword = document.getElementById('room-password');
const purchase = document.getElementById('purchases');
const inventory = document.getElementById('rayons');
const creationModal = document.getElementById('creation-modal');
const ptype = document.getElementById('pType-check');
const createRoom = document.getElementById('createRoom');
const CancelCreationRoom = document.getElementById('CancelRoom');
//QRCODE
const qCodeBtn = document.getElementById('qrcode-btn');

historicSection.hidden = true;
verifySection.hidden = true;
asmbl_btn.disabled = true;
reset_btn.disabled = true;
del_btn.disabled = true;
create_btn.disabled = true;
roomManagement.hidden = true;
roomAssembler.hidden = true;


// INIT FUNCTION
function get_suffix(url) {
    let array = url.split('%26id%3D');
    if (array.length > 1) {
      suffix = '%26id%3D' + array[array.length - 1];
    } else {
      suffix = url.split('/')[url.split('/').length - 1];
    }
    return suffix;
  }