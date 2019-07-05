$(document).ready(function() {

  // submit from after triggering verification
  window.submit_form = function(form) {
    var button = $('<button>').attr('type', 'submit');
    $(form).append(button);
    $(button).click();
    $(button).remove();
  }

	/***************** logging *************/

	// note: only whitelisted actions are logged
	function log_action(type, parameters) {
		fetch('/action', {
			method: 'POST', 
			headers: {'Accept': 'application/json', 'Content-Type': 'application/json'}, 
			body: JSON.stringify({type: type, parameters: parameters})
		}).then(function(res) {
			console.log(res);
		});
	}

	// log typing events
	$('textarea.comment-form').change(function(event) {
		log_action('typed-text', {target: 'comment-form', value: event.target.value});
	});
	$('input.search-bar').change(function() {
		log_action('typed-text', {target: 'search-bar', value: event.target.value});
	});

	/***************** channel checkbox *****************/

	$('input.channel-checkbox').click(function(event) {
		if(event.target.checked) {
			event.target.checked = confirm('Only search in Endeavour channel?');
		}
	});

	/***************** query suggestions ******************/

	var timer = null;
	function get_suggestions(query, sync, async) {
		if(timer != null) clearTimeout(timer);
		timer = setTimeout(function() {
			var prompt = $('#query-prompt').val()
			fetch('/suggest?q=' + escape(query) + '&prompt=' + prompt)
				.then(function(response) {
					return response.json();
				})
				.then(function(data) {
					var source = [];
					for(var i = 0; i < data.length; i++) {
						source.push({'id': i, name: data[i]});
					}
					async(source);
				});
		}, 100);
	}
	$("#query-field").typeahead({
		source: get_suggestions, 
		matcher: function() { return true; },
		afterSelect: function(item) {
			log_action('query-suggestion', {action: 'selected-item', value: item});
		},
		autoSelect: false,
	});

	/***************** endeavour channel checkbox ******************/

	var saved_prompt = 0;
	$('#channel_only').change(function(event) {
		var prompt_select = $('#query-prompt')[0];
		if(event.target.checked) {
			saved_prompt = prompt_select.selectedIndex;
			prompt_select.selectedIndex = 3; // use "(no start)" when checkbox is checked
		} else {
			prompt_select.selectedIndex = saved_prompt;
		}
	});


	/***************** friend selector for sharing ******************/

	function update_checkbox(event) {
		var target = event.target;
		var checked = target.checked;
		if(! $(target).hasClass('disabled')) {
			if(checked) $(target).parent().addClass('btn-secondary').removeClass('btn-light-outline');
			else $(target).parent().removeClass('btn-secondary').addClass('btn-light-outline');
		}
	}
	$('.btn > input[type="checkbox"]').change(update_checkbox).change();

	/***************** speech to text ******************/

	$('.stt-button').each(function(index, button) {
		var target = $('#' + $(button).attr('stt-target'));
		var transcript = '';
		var listening = false;
		
		function on_interim(text) {
			$(target).val(transcript + ' ' + text);
		}

		function on_final(text) {
			transcript += ' ' + text;
			$(target).val(transcript);
			log_action('voice-input', {action: 'transcript', text: text});
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
					log_action('voice-input', {action: 'stop-recording'});
					stt.stopRecording();
				} else {
					log_action('voice-input', {action: 'start-recording'});
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

	var idleTriggerTime = 4;
	var idleLoopTime = 4;
	var idleAnimationDuration = 2;
	var idleTime = 0;

	function resetIdlePrompts() {
		idleTime = 0;
		$('.show-idle-prompt').removeClass('idle');
	}
	$(this).keypress(resetIdlePrompts).mouseover(resetIdlePrompts);
	document.addEventListener('touchmove', resetIdlePrompts);

	var nextIdleElement = 0;
	var idleInterval = setInterval(function() {
		idleTime = idleTime + 1;
		if (idleTime >= idleTriggerTime) {
			var sinceTrigger = idleTime - idleTriggerTime;
			if(sinceTrigger % idleLoopTime == 0) {
				$('.show-idle-prompt').eq_mod(nextIdleElement).addClass('idle');
				nextIdleElement ++;
			} else if(sinceTrigger % idleLoopTime == idleAnimationDuration) {
				$('.show-idle-prompt').removeClass('idle');
			}
		}
	}, 1000);

});
