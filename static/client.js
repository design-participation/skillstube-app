$(document).ready(function() {

	/***************** query suggestions ******************/

	let timer = null;
	function get_suggestions(query, sync, async) {
		if(timer != null) clearTimeout(timer);
		timer = setTimeout(function() {
			let prompt = $('#query-prompt').val()
			fetch('/suggest?q=' + escape(query) + '&prompt=' + prompt)
				.then(function(response) {
					return response.json();
				})
				.then(function(data) {
					let source = [];
					for(var i = 0; i < data.length; i++) {
						source.push({'id': i, name: data[i]});
					}
					async(source);
				});
		}, 100);
	}
	$("#query-field").typeahead({source: get_suggestions, matcher: function() { return true; } });


	/***************** friend selector for sharing ******************/

	function update_checkbox(event) {
		let target = event.target;
		let checked = target.checked;
		if(! $(target).hasClass('disabled')) {
			if(checked) $(target).parent().addClass('btn-secondary').removeClass('btn-light-outline');
			else $(target).parent().removeClass('btn-secondary').addClass('btn-light-outline');
		}
	}
	$('.btn > input[type="checkbox"]').change(update_checkbox).change();

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

	/***************** idle prompts ****************/

	jQuery.fn.random = function() {
    var randomIndex = Math.floor(Math.random() * this.length);  
		console.log(randomIndex);
    return jQuery(this[randomIndex]);
	};

	jQuery.fn.eq_mod = function(index) {
    return jQuery(this[index % this.length]);
	};

	const idleTriggerTime = 4;
	const idleLoopTime = 4;
	const idleAnimationDuration = 2;
	var idleTime = 0;

	function resetIdlePrompts() {
		idleTime = 0;
		$('.show-idle-prompt').removeClass('idle');
	}
	$(this).keypress(resetIdlePrompts).mouseover(resetIdlePrompts);

	var nextIdleElement = 0;
	var idleInterval = setInterval(function() {
		idleTime = idleTime + 1;
		if (idleTime >= idleTriggerTime) {
			let sinceTrigger = idleTime - idleTriggerTime;
			if(sinceTrigger % idleLoopTime == 0) {
				$('.show-idle-prompt').eq_mod(nextIdleElement).addClass('idle');
				nextIdleElement ++;
			} else if(sinceTrigger % idleLoopTime == idleAnimationDuration) {
				$('.show-idle-prompt').removeClass('idle');
			}
		}
	}, 1000);

});
