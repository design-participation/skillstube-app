// based on work by Kevin Gunawan

/* Speech-to-text provider using Webspeech API
 *   - on_final(transcript): called when a final transcript is generated
 *   - on_interim(transcript): called when an interim transcript is generated
 *   - lang: code for the spoken language
*/
function WebSpeechProvider(on_final, on_interim, lang) {
    let SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let provider = {};
		provider.recognition = new SpeechRecognition();
    provider.recognition.continous = true;
    provider.recognition.interimResults = true;
    provider.recognition.lang = lang || 'en-US';
    provider.on_final = on_final;
    provider.on_interim = on_interim || function() { };
    provider.interim_transcript = '';
    provider.final_transcript = '';
    console.log('RECOGNITION', provider.recognition);

    provider.recognition.onstart = function() {
      console.log("Listening");
    };

    provider.recognition.onresult = function(event) {
      provider.interim_transcript = '';
      provider.final_transcript = '';
      console.log(event.results);
      console.log(event.resultIndex);

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
      console.log("Error occured in recognition: " + event.error);
      provider.stopRecording();
    }

  provider.startRecording = function() {
    provider.recognition.start();
    provider.recognition.onend = function() {
      console.log("continue listening");
      provider.recognition.start();
    }
  }

  provider.stopRecording = function() {
    provider.recognition.stop();
    provider.recognition.onend = function() {
      if(provider.final_transcript == '' && provider.interim_transcript != '') provider.on_final(provider.interim_transcript);
      console.log("stopped listening per click");
    }
  }

	return provider;
}

WebSpeechProvider.isSupported = function() {
	return window.SpeechRecognition !== undefined || window.webkitSpeechRecognition !== undefined;
}

/*let secrets = {
  password: 'd3d70f8ecd1347fe8300a9a513126218',
  region: 'eastasia',
}; */

// TODO: get token from server
let secrets = {
  password: '4fbeb80ecd3a4d8ca25fcfbd17232ca4',
  region: 'southeastasia',
};

/* Speech-to-text provider using Microsoft Cognitive Services
 *   - on_final(transcript): called when a final transcript is generated
 *   - on_interim(transcript): called when an interim transcript is generated
 *   - lang: code for the spoken language
 * This component in only supported if microsoft.cognitiveservices.speech.sdk.bundle.js was first loaded in the page.
*/
function MicrosoftSpeechProvider(on_final, on_interim, lang) {
    this.on_final = on_final;
    this.on_interim = on_interim || function() { };
    this.final_transcript = '';
    this.interim_transcript = '';
    var provider = this;

    let SpeechSDK = window.SpeechSDK;
    let speechConfig = SpeechSDK.SpeechConfig.fromSubscription(secrets.password, secrets.region);
    speechConfig.language = lang || 'en-US';
    let audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
    this.recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);

    console.log('RECOGNIZER', this.recognizer);

    this.recognizer.recognizing = function(s, e) {
      console.log('recognizing', e, e.result.text);
      provider.interim_transcript = e.result.text;
      provider.on_interim(provider.interim_transcript);
    };

    this.recognizer.recognized = function(s, e) {
      console.log('recognized', e, e.result.text);
      if(e.result.text !== undefined) {
        provider.final_transcript = e.result.text;
        provider.on_final(provider.final_transcript);
      }
    }

    this.recognizer.canceled = function(s, e) {
      console.log('canceled', e);
      provider.stopRecording();
    }

    this.recognizer.sessionStarted =function (s,e) {
      console.log('sessionStarted', e);
    }

    this.recognizer.sessionStopped =function(s,e) {
      console.log('sessionStopped', e);
    }

    this.recognizer.speechStartDetected =function(s,e) {
      console.log('speechStartDetected', e);
    }

    this.recognizer.speechEndDetected = function(s,e) {
      console.log('speechEndDetected', e);
    }

  this.startRecording = function() {
    this.recognizer.startContinuousRecognitionAsync(
      function() { console.log('started'); },
      function(error) { console.log('start: error', error); }
    );
  }

  this.stopRecording = function() {
    var provider = this;
    this.recognizer.stopContinuousRecognitionAsync(
      function() {
        console.log("stopped listening per click");
        console.log(provider);
        if(provider.final_transcript == '' && provider.interim_transcript != '') provider.on_final(provider.interim_transcript);
      },
      function(error) { console.log('stop: error', error); }
    );
  }

	return this;
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
    return function() {
      this.isSupported = function() { return false; };
    }
  }
}

/*class SpeechToText extends React.Component {
  constructor(props){
    super(props)
    this.state = {message: "Press to Record", listening: false};
    this.toggleListen= this.toggleListen.bind(this);
    this.handleListen = this.handleListen.bind(this);

    let object = this;

    function onFinalResult(transcript) {
      console.log('Final:', transcript);
      object.props.changeCallback({target:{name:object.props.target, value:transcript}});
    }

    function onPartialResult(transcript) {
      console.log('Partial:', transcript);
      object.props.changeCallback({target:{name:object.props.target, value:transcript}});
    }

    this.SpeechToTextProviderClass = SpeechToTextProviderFactory();
    console.log('Using speech-to-text from', this.SpeechToTextProviderClass);
    this.recognizer = new this.SpeechToTextProviderClass(onFinalResult, onPartialResult);
  }

  componentDidMount() {
    console.log(this.recognizer);
  }

  //toggling function to initiate speech recognition. handleListen is called in callback to process the speech recognition logic
  toggleListen() {
    this.setState({
      //stop listening when button is pressed
      listening: !this.state.listening
    },() => {this.handleListen()})
  }

  //speech recognition logic
  handleListen() {
    console.log('listening?', this.state.listening)

    if(this.state.listening){
      this.recognizer.startRecording();
    } else{
      this.recognizer.stopRecording();
    }
  }

  render() {
    return(
      <Button 
        className={"btn btn-secondary" + (this.props.managed ? "" : " speech-recorder-button") + (this.state.listening ? " recording" : "")} 
        onClick={this.toggleListen} 
        disabled={!this.SpeechToTextProviderClass.isSupported()}>
        <i className={"fas fa-microphone" + (this.SpeechToTextProviderClass.isSupported() ? '' : '-slash')}></i>
      </Button>

    )
  }
}*/

//export default SpeechToText;
