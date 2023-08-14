$(document).ready(function() {
	//text in the buttons icons
	const increasePrice = 'arrow_drop_up';
	const reducePrice = 'arrow_drop_down';
	var intervalID;
	const minPriceInput = $('.price-min-filter input[type=text]');
	const maxPriceInput = $('.price-max-filter input[type=text]');
	//price values in the fields while page was load
	const minPriceStart = parseFloat($(minPriceInput).val(), 10);
	const maxPriceStart = parseFloat($(maxPriceInput).val(), 10);

	$(`.adjust-min-price .material-symbols-outlined, .adjust-max-price .material-symbols-outlined`).on('mousedown mouseup', function(event) {
		var currentPushObj = $(this);
		var currentAction = $(currentPushObj).text(); //increase or decrease price
		var currentPriceToChange = $(this).parent().attr('class').includes('max') ? 'max' : 'min'; //change max or min price
		var currentValue;
		var newValue;

		if (event.type === 'mousedown') {
			intervalID = setInterval(function() {
				currentValue = currentPriceToChange === 'min' ? $(minPriceInput).val() : $(maxPriceInput).val(); //current price value in the input

				if (currentAction === reducePrice) {
					newValue = calcNewPriceValue(currentValue, 'down');
				} else if (currentAction === increasePrice) {
					newValue = calcNewPriceValue(currentValue, 'up');
				}

				//checking boundaries of a new value and if it is in boundaries, save it to the field
				var newValueConvert = parseFloat(newValue, 10)
				if ((minPriceStart <= newValueConvert) && (newValueConvert <= maxPriceStart)) {
					$(currentPriceToChange === 'min' ? minPriceInput : maxPriceInput).val(newValue);
				}

			}, 300)
		} else if (event.type === 'mouseup') {
			clearInterval(intervalID);
			intervalID = null;
		}
	})

	//function calculates a new price value, depending on its increase or decrease
	function calcNewPriceValue(newValue, direction) {
		var newConvertedValue = Math.round(Number(newValue)) * 100 //rounding the price to an integer
		if (direction === 'up') {
			return ((newConvertedValue + 1000) / 100).toFixed(2);
		} else if (direction === 'down') {
			return ((newConvertedValue - 1000) / 100).toFixed(2);
		}
	}
})