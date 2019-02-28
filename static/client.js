function update_checkbox(target) {
	let checked = target.checked;
	if(checked)
		$(target).siblings('label').addClass('selected-item');
	else
		$(target).siblings('label').removeClass('selected-item');
}

$(function() {
	$('input[type="checkbox"]').change();
	$('.stt-button').each(function(index, button) {
		let target = $('#' + $(button).attr('stt-target'));
		console.log(button, target);
		function on_interim(text) {
			console.log('interim', text);
			$(target).val(text);
		}
		function on_final(text) {
			console.log('interim', text);
			$(target).val(text);
		}
		let stt = SpeechToTextProviderFactory()(on_final, on_interim);
		let listening = false;
		$(button).click(function() {
			if(listening) {
				stt.stopRecording();
				listening = false;
				$(button).removeClass('stt-recording');
			} else {
				stt.startRecording();
				listening = true;
				$(button).addClass('stt-recording');
			}
		});
	});
});
