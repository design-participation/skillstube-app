var videoDevices = [];

function init_qrcode_scanner(error_callback) {
}

var videoStream = null;
var interval;

function run_qrcode_scanner(result_callback, camera_num) {
	console.log('start qrcode scanner');
	qrcode.callback = function(result) {
		console.log('scan result [' + result + ']');
		result_callback(result);
	}

	let video = document.getElementById('qr-video');
	let canvas = document.getElementById('qr-canvas');
	let context = canvas.getContext('2d');

	$('#choose-camera').popover('dispose');

	// stop previous stream if any
	if(videoStream !== null) {
		video.pause();
		video.srcObject = null;
		let tracks = videoStream.getTracks();
		console.log(tracks);
		for(let i = 0; i < tracks.length; i++) tracks[i].stop();
		clearInterval(interval);
	}

  // update list of devices
  navigator.mediaDevices.enumerateDevices()
    .then(function(devices) {
      videoDevices = [];
      devices.forEach(function(device) {
        if(device.kind == 'videoinput') {
          console.log(device);
          videoDevices.push(device);
        }
      });
      if(videoDevices.length == 0) throw "No video device found";
      let device = videoDevices[camera_num % videoDevices.length];
      let constraints = {video: {width: 320, height: 240, deviceId: device.deviceId}};
      return navigator.mediaDevices.getUserMedia(constraints);
    })
    .then(function(stream) {
      videoStream = stream;
      video.srcObject = stream;
      video.play();
      interval = setInterval(function() {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);
        try {
          qrcode.decode();
        } catch(error) {
          //console.log(error);
        }
      }, 250)
    }).catch(function(error) {
      console.log('Video capture error: ', error);
      console.log($('#choose-camera'));
      $('#choose-camera').popover('dispose').popover({html: true, content: '<i style="color: var(--danger)" class="fas fa-times-circle"></i> Did you allow video recording?', placement: 'top'}).popover('show');
    });
}

function stop_qrcode_scanner() {
	console.log('stop qrcode scanner');
	let video = document.getElementById('qr-video');
	if(videoStream !== null) {
		video.pause();
		video.srcObject = null;
		let tracks = videoStream.getTracks();
		for(let i = 0; i < tracks.length; i++) tracks[i].stop();
		clearInterval(interval);
	}
}
