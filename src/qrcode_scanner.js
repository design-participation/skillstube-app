var videoDevices = [];
var videoStream = null;
var interval;

function qrcode_file_fallback() {
}

function run_qrcode_scanner(result_callback, camera_num) {
  console.log('start qrcode scanner');

	qrcode.callback = function(result) {
		console.log('scan result [' + result + ']');
		result_callback(result);
	};

	var video = document.getElementById('qr-video');
	var canvas = document.getElementById('qr-canvas');
	var context = canvas.getContext('2d');
  $(canvas).hide();

	$('#choose-camera').popover('dispose');

  if(!navigator.mediaDevices) { // file input fallback
    $('#qr-image-picker').val(null);
    $('#qr-image-picker').change(function() {
      var url = URL.createObjectURL(document.getElementById('qr-image-picker').files[0]);
      var image = new Image();
      image.src = url;
      image.onload = function() {
        $(canvas).show();
        canvas.width = image.width;
        canvas.height = image.height;
        context.drawImage(image, 0, 0);
        try {
          qrcode.decode();
        } catch(error) {
          //console.log(error);
        }
      };
    });
    return;
  }
  $('#qr-image-picker').hide();
  $('#qr-video-container').show();
  $('#choose-camera').show();

	// stop previous stream if any
	if(videoStream !== null) {
		video.pause();
		video.srcObject = null;
		var tracks = videoStream.getTracks();
		console.log(tracks);
		for(var i = 0; i < tracks.length; i++) tracks[i].stop();
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
      var device = videoDevices[camera_num % videoDevices.length];
      var constraints = {video: {width: 320, height: 240, deviceId: device.deviceId}};
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
	var video = document.getElementById('qr-video');
	if(videoStream !== null) {
		video.pause();
		video.srcObject = null;
		var tracks = videoStream.getTracks();
		for(var i = 0; i < tracks.length; i++) tracks[i].stop();
		clearInterval(interval);
	}
}
