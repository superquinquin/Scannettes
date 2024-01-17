
const socket = io.connect(config.address);
const IDInput = document.getElementById('identifiant')
const passwordInput = document.getElementById('password')
const errorMsg = document.getElementById('error-msg')
const connectionBtn = document.getElementById('connection-btn')


