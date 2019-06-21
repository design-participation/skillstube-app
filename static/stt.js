// based on work by Kevin Gunawan, Benoit Favre

/* Speech-to-text provider using Webspeech API
 *   - on_final(transcript): called when a final transcript is generated
 *   - on_interim(transcript): called when an interim transcript is generated
 *   - lang: code for the spoken language
 * https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API
 * Currently, only Chrome browsers are supported
 */
function WebSpeechProvider(on_final, on_interim, on_state_change, lang) {
	let SpeechRecognitionImpl = window.SpeechRecognition || window.webkitSpeechRecognition;
	let provider = {};

	provider.on_final = on_final;
	provider.on_interim = on_interim || function() { };
	provider.on_state_change = on_state_change || function() { };
	provider.interim_transcript = '';
	provider.final_transcript = '';

	provider.init = function() {
		console.log('stt: init');
		provider.recognition = new SpeechRecognitionImpl();
		provider.recognition.continous = true;
		provider.recognition.interimResults = true;
		provider.recognition.lang = lang || 'en-US';
		provider.recognition.onstart = function() {
			provider.on_state_change('start');
		};

		provider.recognition.onresult = function(event) {
			provider.interim_transcript = '';
			provider.final_transcript = '';
			console.log('stt: transcript', event);

			for(let i = event.resultIndex; i < event.results.length; i++) {
				const transcript = event.results[i][0].transcript;
				if(event.results[i].isFinal) {
					provider.final_transcript += ' ' + transcript;
				} else{
					provider.interim_transcript += transcript;
				}
			}
			if(provider.interim_transcript != '') provider.on_interim(provider.interim_transcript);
			if(provider.final_transcript != '') provider.on_final(provider.final_transcript);
		}
		provider.recognition.onerror = function(event) {
			console.log("stt: error", event);
			let error = event.error;
			if(error == 'no-speech' || error == 'aborted') {
				// should continue recording
			} else {
				provider.on_state_change('unavailable', error);
				setTimeout(function() {
					console.log('stt: attempt reinit');
					provider.init();
				}, 5000);
			}
			provider.stopRecording();
		}

		console.log('stt: engine', provider.recognition);
		provider.on_state_change('available');
	}

	provider.startRecording = function() {
		provider.recognition.start();
		provider.recognition.onend = function() {
			console.log("stt: continue recording");
			provider.recognition.start();
		}
	}

	provider.stopRecording = function() {
		provider.recognition.stop();
		provider.recognition.onend = function() {
			if(provider.final_transcript == '' && provider.interim_transcript != '') provider.on_final(provider.interim_transcript);
			console.log("stt: stopped recording");
			provider.on_state_change('end');
		}
	}

	provider.isSupported = function() { return true; }
	provider.init();

	return provider;
}

WebSpeechProvider.isSupported = function() {
	return window.SpeechRecognition !== undefined || window.webkitSpeechRecognition !== undefined;
}

/* Speech-to-text provider using Microsoft Cognitive Services
 *   - on_final(transcript): called when a final transcript is generated
 *   - on_interim(transcript): called when an interim transcript is generated
 *   - lang: code for the spoken language
 * This component in only supported if microsoft.cognitiveservices.speech.sdk.bundle.js was first loaded in the page.
 * see https://github.com/Azure-Samples/cognitive-services-speech-sdk/blob/master/samples/js/browser/index.html
 * The server provides tokens valid for 10 minutes at GET /stt/microsoft.
 */
function MicrosoftSpeechProvider(on_final, on_interim, on_state_change, lang) {
	let provider = {};
	provider.on_final = on_final;
	provider.on_interim = on_interim || function() { };
	provider.final_transcript = '';
	provider.on_state_change = on_state_change || function() { };
	provider.interim_transcript = '';

	let SpeechSDKImpl = window.SpeechSDK;

	provider.init = function() {
		console.log('stt: init');
		provider.renew_token();
	}
	
	provider.renew_token = function() {
		console.log('stt: renew token');
		fetch('/stt/microsoft')
			.then(response => {
				return response.text();
			}).then(text => {
				var token = JSON.parse(atob(text.split('.')[1]));
				region = token.region;
				provider.init_from_token(text, region);
			})
			.catch(function(error) {
				console.log('stt get token error:', error);
				provider.on_state_change(error);
			}
		);
		// renew access token every 9 minutes (note that this may 
		setTimeout(provider.renew_token, 9 * 60 * 1000);
	}

	provider.init_from_token = function(token, region) {
		console.log('stt: init from token');
		//let speechConfig = SpeechSDKImpl.SpeechConfig.fromSubscription(secrets.password, secrets.region);
		let speechConfig = SpeechSDKImpl.SpeechConfig.fromAuthorizationToken(token, region);
		speechConfig.language = lang || 'en-US';
		let audioConfig = SpeechSDKImpl.AudioConfig.fromDefaultMicrophoneInput();
		provider.recognizer = new SpeechSDKImpl.SpeechRecognizer(speechConfig, audioConfig);

		provider.recognizer.recognizing = function(s, e) {
			console.log('stt: recognizing', e, e.result.text);
			provider.interim_transcript = e.result.text;
			provider.on_interim(provider.interim_transcript);
		};

		provider.recognizer.recognized = function(s, e) {
			console.log('stt: recognized', e, e.result.text);
			if(e.result.text !== undefined) {
				provider.final_transcript = e.result.text;
				provider.on_final(provider.final_transcript);
			}
		}

		provider.recognizer.canceled = function(s, e) {
			// for some reason, we do not get a canceled event when the network disconnects
			console.log('stt: canceled', e);
			if(e.reason == 0) {
				provider.on_state_change('unavailable', e.errorDetails);
				setTimeout(function() {
					console.log('stt: attempt reinit');
					provider.init();
				}, 5000);
			} else {
				provider.on_state_change('end');
			}
		}

		provider.recognizer.sessionStarted = function (s,e) {
			console.log('stt: sessionStarted', e);
			provider.on_state_change('start', e);
		}

		provider.recognizer.sessionStopped = function(s,e) {
			console.log('stt: sessionStopped', e);
			provider.on_state_change('end', e);
		}

		provider.recognizer.speechStartDetected = function(s,e) {
			console.log('stt: speechStartDetected', e);
		}

		provider.recognizer.speechEndDetected = function(s,e) {
			console.log('stt: speechEndDetected', e);
			// TODO: continue?
		}

		console.log('stt: engine', provider.recognizer);
		provider.on_state_change('available');
	}

	provider.startRecording = function() {
		provider.recognizer.startContinuousRecognitionAsync(
			function() { console.log('started'); },
			function(error) { 
				console.log('stt: error while stopping', error); 
				provider.on_state_change(error); 
			}
		);
	}

	provider.stopRecording = function() {
		provider.recognizer.stopContinuousRecognitionAsync(
			function() {
				console.log('stt: stopped recording');
				if(provider.final_transcript == '' && provider.interim_transcript != '') provider.on_final(provider.interim_transcript);
				provider.on_state_change('end'); 
			},
			function(error) { 
				console.log('stt: error while stopping', error); 
				provider.on_state_change('end', error); //should it be unavailable?
			}
		);
	}

	provider.isSupported = function() { return true; }
	provider.init();

	return provider;
}

MicrosoftSpeechProvider.isSupported = function() {
	return window.SpeechSDK !== undefined;
}

/* Factory for instanciating a supported speech-to-text provider
*/
function SpeechToTextProviderFactory() {
	if(WebSpeechProvider.isSupported()) {
		return WebSpeechProvider;
	} else if(MicrosoftSpeechProvider.isSupported()) {
		return MicrosoftSpeechProvider;
	} else {
		return function(on_final, on_interim, on_state_change, lang) {
			this.isSupported = function() { return false; };
			this.startRecording = function() { console.log('stt: unsupported'); };
			this.stopRecording = function() { console.log('stt: unsupported'); };
			on_state_change('unavailable');
		}
	}
}

