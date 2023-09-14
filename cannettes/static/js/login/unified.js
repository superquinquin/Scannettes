var config = {"ADDRESS": "http://localhost:5000", "COLOR_PRIMARY": "#fefa85", "COLOR_SECONDARY": "#3C312E", "COLOR_TERNARY": "#FAEFEF", "COLOR_NEW_ITEMS": "#FD8789", "COLOR_NEW_ITEMS_IF_EXIST": "#B5B3D0", "COLOR_MOD_ITEMS": "#FDC087", "COLOR_NORMAL_ITEMS": "#CFF2E8", "CAMERA_ENABLE_VIDEO": true, "CAMERA_ENABLE_AUDIO": false, "CAMERA_IDEAL_WIDTH": 1920, "CAMERA_IDEAL_HEIGHT": 1080, "CAMERA_IDEAL_MODE": "environment", "CAMERA_FRAME_WIDTH": 300, "CAMERA_FRAME_HEIGHT": 200, "CAMERA_FPS": 120, "CAMERA_PKG_FREQUENCY": 2};


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

var browser = get_browser_id()
var socket = io.connect(config.ADDRESS);

socket.on('connect', function() {
  console.log('is in loggin');
  socket.emit('message', {data: 'in logger'});
});

const IDInput = document.getElementById('identifiant')
const passwordInput = document.getElementById('password')
const errorMsg = document.getElementById('error-msg')
const connectionBtn = document.getElementById('connection-btn')

connectionBtn.onclick = function () { 
  let id = IDInput.value;
  let password = passwordInput.value;
  socket.emit('ask_permission', {'id': id, 'password': password, 'browser':browser})
}

socket.on('permission', (context) => {
  if (context.permission == true) {
    window.location = context.url;
  } else {
    passwordInput.value = '';
    errorMsg.innerHTML = 'Votre identifiant ou mot de passe est erroné'
  }
});
