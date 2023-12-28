

var initialized = false;
const socket = io.connect(config.address);





socket.on("connect", function() {
    if (!initialized) {
        initialized = true;
        socket.emit('initialization_call');
    }
});

socket.on("initialization", function(context) {
    console.log(context);
});