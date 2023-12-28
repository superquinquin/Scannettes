

var initialized = false;
const params = new URLSearchParams(window.location.search);
const rid = params.get("rid");

const socket = io.connect(config.address);

socket.on("connect", function() {
    if (!initialized) {
        initialized = true;
        socket.emit('admin-initialization-call', {"instance": "room", "rid": parseInt(rid)});
    }
});

socket.on("room-initialization", function(context) {
    console.log(context);
});





//////////////////////////////  COLLAPSING BLOCKS

const collapser = document.getElementsByClassName("collaps-block");
for (var i = 0; i < collapser.length; i++) {
  collapser[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display == 'flex'){
      content.style.display = 'none';
    } else {
      content.style.display = 'flex';
    } 
  });
}