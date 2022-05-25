
const FPS = config.CAMERA_FPS;
const CPF = config.CAMERA_PKG_FREQUENCY
const croppedWidth = config.CAMERA_FRAME_WIDTH;
const croppedHeight = config.CAMERA_FRAME_HEIGHT;

var streaming = false;

const modal_btn = document.getElementById("display_modal");
const modal = document.getElementById("modal");
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d', { alpha: false });

const croppedCanvas = document.getElementById('cropped-canvas');
const croppedCTX = croppedCanvas.getContext('2d', { alpha: false });
croppedCTX.canvas.hidden = true;

// MODAL LASER
const modal_laser_btn = document.getElementById('display_laser');
const modal_laser = document.getElementById('modal-laser');
const laserOutput = document.getElementById('laser-output')


// CAMERA SCANNER MODAL APPLICATION
modal_btn.onclick = async function () { 
  display = modal.style.display;
  if(!display | display == 'none'){
    console.log('oppening modal & start streaming')

    modal.style.display = 'flex';
    document.getElementById('html').style.overflowY = 'hidden';
    modal_laser_btn.disabled = true;

    streaming = true;
    video = document.querySelector("#videoElement");

    if (navigator.mediaDevices.getUserMedia) {
      var stream = await navigator.mediaDevices.getUserMedia({ video:      config.CAMERA_ENABLE_VIDEO,
                                                               audio:      config.CAMERA_ENABLE_AUDIO, 
                                                               width:      { ideal: config.CAMERA_IDEAL_WIDTH }, 
                                                               height:     { ideal: config.CAMERA_IDEAL_HEIGHT },
                                                               facingMode: { ideal: config.CAMERA_IDEAL_MODE }})
      video.srcObject = stream;
      WIDTH = stream.getVideoTracks()[0].getSettings().width;
      HEIGHT = stream.getVideoTracks()[0].getSettings().height;
    } 
    

    canvas.width = video.width = WIDTH;
    canvas.height = video.height = HEIGHT;
    croppedCanvas.width = croppedWidth;
    croppedCanvas.height = croppedHeight;
    ctx.lineWidth = 3;
    ctx.strokeStyle = "blue";
    var cropX = Math.trunc(Math.abs(video.width - croppedWidth) / 2);
    var cropY = Math.trunc(Math.abs(video.height - croppedHeight) / 2);
    let frame_counter = 0;
    let color_counter = 0;

    setInterval(() => {
      if(streaming) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        if (ctx.strokeStyle === '#1df700' && color_counter < 16) {
          color_counter += 1;
        } else if (ctx.strokeStyle === '#1df700' && color_counter == 16) {
          ctx.strokeStyle = "blue";
          color_counter = 0;
        }

        draw_corner(cropX, cropY, 40, 'topleft');
        draw_corner(cropX, cropY + croppedHeight, 40, 'bottomleft');
        draw_corner(cropX + croppedWidth, cropY, 40, 'topright');
        draw_corner(cropX + croppedWidth, cropY + croppedHeight, 40, 'bottomright');

        croppedCTX.drawImage(video,cropX, cropY, croppedWidth, croppedHeight, 0, 0, croppedWidth, croppedHeight);

        if(frame_counter == CPF) {

          let pixels = croppedCTX.getImageData(0, 0, croppedWidth, croppedHeight).data;
          let grayscaleArray = [];
          for (var i = 0; i < pixels.length; i += 4) {
            let pixelIntensity = parseInt((pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3);
            grayscaleArray.push(pixelIntensity)
          }
          var B64Image = btoa(String.fromCharCode.apply(null, new Uint8Array(grayscaleArray)));
          var data = {'image': B64Image, 'id': roomID};
          socket.emit('image', data);
          frame_counter = 0;
        } else {
          frame_counter += 1;
        }
      } else {
        clearInterval();
      }
    }, 10000/FPS);

  }else {
    console.log('closing modal & stop streaming');
    modal.style.display = 'none';
    document.getElementById('html').style.overflowY = 'visible';
    modal_laser_btn.disabled = false;
    stopStreamedVideo(video);
    streaming = false;

    // socketio abnormal behavior after closing one time the camera modal
    // socketio jam itself by refusing sending the data to the server while the camera is on stream
    // right after the camera stream get off again, the socket send all the data to the server.
    // later use have the same problem. just first camera use works as intended.
    // However, it is not considered an error.

    // curent tricks: reloading the page while leaving the modal. Hope to find better
    location.reload();
  }
}


function draw_corner(X,Y, len, place) {
  ctx.beginPath();

  ctx.moveTo(X, Y);
  if (place === 'bottomleft' || place === 'bottomright') {
    ctx.lineTo(X, Y - len);
  } else {
    ctx.lineTo(X, Y + len);
  }

  ctx.moveTo(X, Y);
  if (place === 'topright' || place === 'bottomright') {
    ctx.lineTo(X - len, Y);
  } else {
    ctx.lineTo(X + len, Y);
  }
  ctx.stroke();
}


function stopStreamedVideo(videoElem) {
  var stream = videoElem.srcObject;
  var tracks = stream.getTracks();

  tracks.forEach(function(track) {
    track.stop();
  });

  videoElem.srcObject = null;
}


socket.on('change_color', function() {
  ctx.strokeStyle = "#1df700";
});




/////////////////////////////////////////// LASER SCANNER
var doubleScanBlocker = false;
var lastScanned = '';

modal_laser_btn.onclick =  function () {

  if (modal_laser.style.display != 'flex') {
    modal_laser.style.display = 'flex';
    document.getElementById('html').style.overflowY = 'hidden';
    modal_btn.disabled = true;
    laserOutput.value = "";
    laserOutput.focus()


    //KEEP FOCUS
    if (modal_laser.style.display == 'flex') {
      document.getElementsByTagName("body")[0].addEventListener("click", keepLaserFocus);

    }
    
    if (document.activeElement === laserOutput) {
      window.addEventListener("keydown", function (e) {
        if (e.key != 'Shift' & e.key != 'Enter' & /^-?\d+$/.test(e.key)) {
          if (document.activeElement === laserOutput) {
            // tricks to make sure not writing ean number wwhile modifying qty
            laserOutput.value += e.key
          }
        }
      });
    }


    // SENDING SCANNER OUTPUT
    laserOutput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        console.log('has pressed enter')
        let barcode = laserOutput.value;
        let data = {'barcode': barcode, 'id': roomID};

        console.log(barcode)
        if (((lastScanned != '' & barcode != lastScanned) | lastScanned == '')) {
          console.log('in', barcode, lastScanned)
          if (barcode != '') {
            socket.emit('laser', data);
            lastScanned = barcode;
          }
        } 
        
        laserOutput.value = "";
      }
    });

  } else {
    modal_laser.style.display = 'none';
    document.getElementById('html').style.overflowY = 'visible';
    modal_btn.disabled = false;
  }
  
}

function keepLaserFocus(e) {
  if (e.path[0].className != 'mod-input') {
    laserOutput.focus()
  }
}