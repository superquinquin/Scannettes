var config = {"colors": {"primary": "#fefa85", "secondary": "#3C312E", "ternary": "#FAEFEF", "new_items": "#FD8789", "new_items_if_exist": "#B5B3D0", "mod_items": "#FDC087", "normal_items": "#CFF2E8"}, "enable_video": true, "enable_audio": false, "ideal_width": 1920, "ideal_height": 1080, "ideal_mode": "environment", "frame_width": 300, "frame_height": 200, "fps": 120, "pkg_frequency": 2, "static_url": "/static", "secret_key": "xxxxxxx", "application_root": "/", "address": "http://localhost:5000", "host": "http://localhost", "port": "5000", "debug": false, "testing": false, "templates_auto_reload": true};


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
var socket = io.connect(config.address);

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
  // socket.emit('authenticate', {'username': id, 'password': password})
}

socket.on('on-authentication', (context) => {
  console.log(context);
  if (context.auth.status == "success") {
    console.log("set cookie")
    document.cookie = context.auth.cookie;
    console.log(document.cookie);
    // window.location = context.redirect;

  } else {
    passwordInput.value = '';
    errorMsg.innerHTML = context.auth.reasons;
  }
});

