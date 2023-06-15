$(document).ready(function() {
	var statuses = getStatusDiscounts(); //статусы применения скидок

    /* отображение(скрытие) формы и активация(деактивация) checkbox при загрузке страницы,
    когда купон(карта) были применены(отменены) */
	for (const [key, value] of Object.entries(statuses)) {
		var formId = key.split('-btn')[0];
		var checkBox = $(`[id$=${formId}], [id$=${formId.split('-')[1]}]`);
		if (value === 'Apply') {
			$(`#${formId}-form`).hide();
			$(checkBox).prop('checked', false);
		} else if (value === 'Cancel') {
			$(`#${formId}-form`).show();
			$(checkBox).prop('checked', true);
		}
	};

	$('#have-coupon, #have-card').click(function() {
		//проверка, выбран ли какой либо checkbox
		switch (this.checked) {
			case true:
				if ($(this).attr('id').endsWith('coupon')) {
					$('#coupon-form').show();
					$('#have-card').prop('disabled', true);
				} else if ($(this).attr('id').endsWith('card')) {
					$('#present-card-form').show();
					$('#have-coupon').prop('disabled', true);
				}
				$(this).parent().nextAll().filter('.errorlist').eq(0).show(); //отображение ошибок возле формы
				break;

			case false:
				if ($(this).attr('id').endsWith('coupon')) {
					$('#coupon-form').hide();
					$('#have-card').prop('disabled', false);
				} else if ($(this).attr('id').endsWith('card')) {
					$('#present-card-form').hide();
					$('#have-coupon').prop('disabled', false);
				}
				$(this).parent().nextAll().filter('.errorlist').eq(0).hide(); //скрытие ошибок возле формы
				break;
		}
	})
	//получение статусов кнопок для применения/отмены купона или подарочной карты
	function getStatusDiscounts() {
		var dict = {};
		const statuses = $('.coupon-btn, .present-card-btn').map(function() {
			return dict[$(this).attr('class')] = $(this).text().trim();
		}).get();

		return dict;
	}
})