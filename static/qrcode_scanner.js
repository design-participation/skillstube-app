
function init_qrcode_scanner(error_callback) {
	window.navigator = window.navigator || {};
	navigator.getUserMedia = navigator.getUserMedia       ||
		navigator.webkitGetUserMedia ||
		navigator.mozGetUserMedia    ||
		null;
	if(navigator.getUserMedia === null) {
		console.log('getUserMedia unsupported');
		error_callback();
	}
}

var videoStream = null;
var interval;

function run_qrcode_scanner(result_callback) {
	console.log('start qrcode scanner');
	qrcode.callback = function(result) {
		console.log('scan result [' + result + ']');
		result_callback(result);
	}

	let video = document.getElementById('qr-video');
	let canvas = document.getElementById('qr-canvas');
	let context = canvas.getContext('2d');

	navigator.getUserMedia({
		video: {width: {exact: 320}, height: {exact: 240}}
	}, function(stream) {
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

	}, function(error) {
		console.log('Video capture error: ', error.code);
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
