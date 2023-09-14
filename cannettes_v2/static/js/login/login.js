
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
  socket.emit('authenticate', {'username': id, 'password': password})
}

socket.on('on-authentication', (context) => {
  console.log(context);
  if (context.auth.status == "success") {
    console.log("set cookie")
    document.cookie = context.auth.cookie;
    window.location = context.redirect;
  } else {
    passwordInput.value = '';
    errorMsg.innerHTML = context.auth.reasons;
  }
});
