$(function() {

	/***************** friend selector for sharing ******************/

	function update_checkbox(event) {
		let target = event.target;
		let checked = target.checked;
		if(! $(target).hasClass('disabled')) {
			if(checked) $(target).parent().addClass('btn-success').removeClass('btn-success-outline');
			else $(target).parent().removeClass('btn-success').addClass('btn-success-outline');
		}
	}
	$('input[type="checkbox"]').change(update_checkbox).change();

	/***************** speech to text ******************/

	$('.stt-button').each(function(index, button) {
		let target = $('#' + $(button).attr('stt-target'));
		let transcript = '';
		let listening = false;
		
		function on_interim(text) {
			$(target).val(transcript + ' ' + text);
		}

		function on_final(text) {
			transcript += ' ' + text;
			$(target).val(transcript);
		}

		function on_state_change(state, error) {
			console.log('state change:', state, error);
			if(state == 'start') {
				if(!listening) {
					transcript = '';
					$(button).addClass('stt-recording');
					$(button).popover('dispose').popover({content: 'Click to stop recording.', placement: 'top'}).popover('show');
					listening = true;
				}
			} else if(state == 'end') {
				if(listening) {
					$(button).removeClass('stt-recording');
					$(button).popover('dispose');
					listening = false;
				}
			} else if(state == 'available') {
				$(button).find('i').removeClass('fa-microphone-slash');
				$(button).find('i').addClass('fa-microphone');
				$(button).removeClass('disabled');
				$(button).popover('dispose');
			} else if(state == 'unavailable') {
				$(button).find('i').removeClass('fa-microphone');
				$(button).find('i').addClass('fa-microphone-slash');
				$(button).addClass('disabled');
				if(listening) {
					console.log('was listening');
					$(button).removeClass('stt-recording');
					$(button).popover('dispose').popover({html: true, content: '<i style="color: var(--danger)" class="fas fa-times-circle"></i> Error: ' + error, placement: 'bottom'}).popover('show');
					listening = false;
				}
			}
		}

		var stt = SpeechToTextProviderFactory()(on_final, on_interim, on_state_change);
		if(stt.isSupported()) {
			$(button).click(function() {
				if(listening) {
					stt.stopRecording();
				} else {
					stt.startRecording();
				}
			});
		}
	});
});
