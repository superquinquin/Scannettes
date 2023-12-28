

var initialized = false;
const params = new URLSearchParams(window.location.search);
const rid = params.get("rid");

const socket = io.connect(config.address);

socket.on("connect", function() {
    if (!initialized) {
        initialized = true;
        socket.emit('initialization-call', {"instance": "room", "rid": rid});
    }
});
