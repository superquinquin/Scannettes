

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
  socket.emit('ask_permission', {'id': id, 'password': password})
}

socket.on('permission', (context) => {
  if (context.permission == true) {
    window.location = context.url;
  } else {
    passwordInput.value = '';
    errorMsg.innerHTML = 'Votre identifiant ou mot de passe est erroné'
  }
});