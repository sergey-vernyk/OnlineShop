$(document).ready(function() {
	//текст на значках кнопок
	const increasePrice = 'arrow_drop_up';
	const reducePrice = 'arrow_drop_down';
	var intervalID;
	const minPriceInput = $('.price-min-filter input[type=text]');
	const maxPriceInput = $('.price-max-filter input[type=text]');
	//цены в полях в момент загрузки страницы
	const minPriceStart = parseFloat($(minPriceInput).val(), 10);
	const maxPriceStart = parseFloat($(maxPriceInput).val(), 10);

	$(`.adjust-min-price .material-symbols-outlined, .adjust-max-price .material-symbols-outlined`).on('mousedown mouseup', function(event) {
		var currentPushObj = $(this);
		var currentAction = $(currentPushObj).text(); //увеличить или уменьшить цену
		var currentPriceToChange = $(this).parent().attr('class').includes('max') ? 'max' : 'min'; //изменять макс. или мин. цену
		var currentValue;
		var newValue;

		if (event.type === 'mousedown') {
			intervalID = setInterval(function() {
				currentValue = currentPriceToChange === 'min' ? $(minPriceInput).val() : $(maxPriceInput).val(); //текущее значение цены в input

				if (currentAction === reducePrice) {
					newValue = calcNewPriceValue(currentValue, 'down');
				} else if (currentAction === increasePrice) {
					newValue = calcNewPriceValue(currentValue, 'up');
				}

				//проверка границ нового значения и его запись в поле, если оно в границах
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

	//функция рассчитывает новое значение цены, в зависимости от ее уменьшения или увеличения
	function calcNewPriceValue(newValue, direction) {
		var newConvertedValue = Math.round(Number(newValue)) * 100 //округление цены до целого числа
		if (direction === 'up') {
			return ((newConvertedValue + 1000) / 100).toFixed(2);
		} else if (direction === 'down') {
			return ((newConvertedValue - 1000) / 100).toFixed(2);
		}
	}
})