$(document).ready(function() {
	var listInputs = $('[id^=id_code]'); //все input в блоке
	var initialCurrentAmountPrice = Number($('.amount-items > span:nth-child(2)').text().slice(1)).toFixed(2);

	//делаем неактивные и с другим цветом кнопки для подтверждения формы
	for (var i = 0; i < listInputs.length; i++) {
		if (!$(listInputs[i]).val()) {
			$(listInputs[i]).closest('form').find('button').css({
				'pointer-events': 'none',
				'background-color': '#BFC0C0',
				'color': '#DCDFE1'
			});
		};
	}

	//отслеживания ввода в поле для каждого input
	$('[id^=id_code]').on('input', function() {
		$(this).closest('form').find('button').css({
			'pointer-events': 'all',
			'background-color': 'transparent',
			'color': 'black'
		});
		if (!$(this).val()) {
			$(this).closest('form').find('button').css({
				'pointer-events': 'none',
				'background-color': '#BFC0C0',
				'color': '#DCDFE1'
			});
		}
	});

	//отслеживание подтверждения формы для кода
	$('#coupon-form, #present-card-form').on('submit', function(event) {
		event.preventDefault();
		var currentForm = $(this);
		var submitBtn = $(this).find(':submit');
		var action = submitBtn.text().trim(); //действие берется с названия кнопки с формы
		var url;
		var boundErrorList = $(this).parent().find('.errorlist'); //список ошибок, связанных с выбранной формой

		//применение купона/карты или отмена применения
		if (action === 'Apply') {
			url = $(this).data('url-apply');
		} else if (action === 'Cancel') {
			url = $(this).data('url-cancel');
		}
		var code = $(this).find(':text').val(); //код купона/подарочной карты
		var token = $(this).find(':hidden').val();

		$.ajax({
			url: url,
			method: 'POST',
			data: {
				code: code,
				csrfmiddlewaretoken: token,
			},
			success: function(response) {
				//список всех цен товаров из корзины
				var allProductsPrices = $('.item-price').map(function() {
					return Number($(this).text().trim().slice(1));
				}).get();

				//сумма всех этих цен
				var totalPriceWithoutDiscounts = allProductsPrices.reduce(function(x, y) {
					return x + y;
				});

				//текущая стоимость товаров со всеми скидками
				var currentAmountPrice;
				if($('.amount-items > span:nth-child(2)').text() === 'Free') {
					currentAmountPrice = initialCurrentAmountPrice;
				} else {
					currentAmountPrice = Number($('.amount-items > span:nth-child(2)').text().slice(1)).toFixed(2)
				}

				var finallyPriceWithCoupon = 0;
				var finallyPriceWithCard = 0;
				var formErrors = response['form_errors'];
				//если есть ошибки в форме
				if (formErrors) {
					var error = formErrors['code'][0];
					//если еще не было отображено ошибок
					if(!boundErrorList.has('li').length) {
					    //добавление ошибки в список ошибок в шаблоне
					    $(boundErrorList).prepend(`<li style="text-align: left;">${error}</li>`);
					}
				} else {
					$(boundErrorList).find('li').remove(); //удаление элемента списка с ошибкой
                    //применение скидок
					if (action === 'Apply') {
						submitBtn.text('Cancel');
						//применен купон
						if ($(currentForm).attr('id') === 'coupon-form') {
							var couponDiscount = response['coupon_discount'];
							finallyPriceWithCoupon = totalPriceWithoutDiscounts - (totalPriceWithoutDiscounts * Number(couponDiscount)).toFixed(2);
							initialCurrentAmountPrice = finallyPriceWithCoupon;
							$('.amount-items > span:nth-child(2), .total-price').text('$' + finallyPriceWithCoupon.toFixed(2));
						}
						//применена карта
						if ($(currentForm).attr('id') === 'present-card-form') {
							var cardAmount = response['card_amount'];
							finallyPriceWithCard = currentAmountPrice - Number(cardAmount);
							initialCurrentAmountPrice = finallyPriceWithCard;
							$('.amount-items > span:nth-child(2), .total-price').text(finallyPriceWithCard > 0 ? `$${finallyPriceWithCard.toFixed(2)}` : 'Free');
						}

						//контент появляется, когда применяется одна из скидок
						var contentSummary = `<div class="discounts-total">
                                                  <div class="discount-title">Amount discounts:</div>
                                                  <div class="discount-value">-$${(currentAmountPrice - (finallyPriceWithCoupon || finallyPriceWithCard)).toFixed(2)}</div>
                                              </div>
                                              <div class="without-discounts">
                                                  <div class="without-title">Without discounts:</div>
                                                  <div class="without-value">$${currentAmountPrice}</div>
                                              </div>`

						//вставка значка об успешном применении купона или карты
						$(currentForm).append('<span class="material-symbols-outlined">check_circle</span>');

						//если была применена только одна из скидок
						if (!$('.block-totals').children('.discounts-total, .without-discounts').length) {
							$('.block-summary').after(contentSummary); //добавление информации о размере скидки и стоимости без скидки вниз блока

							//если второй скидкой была подарочная карта
						} else if (finallyPriceWithCard) {
							var curDiscVal = Number($('.discount-value').text().slice(2)); //текущее значение скидки
							var finallyDiscVal = (curDiscVal + Number(cardAmount)).toFixed(2) //окончательное значение скидки
							$('.discounts-total > .discount-value').replaceWith(
								`<div class="discount-value">
                                    -$${finallyDiscVal}
                                </div>`
							);

							//если второй скидкой был купон
						} else if (finallyPriceWithCoupon) {
							var curDiscVal = Number($('.discount-value').text().slice(2)); //текущее значение скидки
							var finallyDiscVal = (curDiscVal + (totalPriceWithoutDiscounts * Number(couponDiscount))).toFixed(2); //окончательное значение скидки
							$('.discounts-total > .discount-value').replaceWith(
								`<div class="discount-value">
                                    -$${finallyDiscVal}
                                </div>`
							);
							//окончательная стоимость со скидками вверху блока
							$('.amount-items > span:nth-child(2)').text('$' + (totalPriceWithoutDiscounts - finallyDiscVal))
						}

					} else if (action === 'Cancel') {
						submitBtn.text('Apply');
						var restDisc; //оставшаяся сумма скидки
						//отменен купон
						if ($(currentForm).attr('id') === 'coupon-form') {
							var discVal = Number(totalPriceWithoutDiscounts * response['coupon_discount']).toFixed(2);
							restDisc = (Number($('.discounts-total > .discount-value').text().trim().slice(2)) - discVal).toFixed(2);
							$('.discounts-total > .discount-value').text('-$' + restDisc); //обновления суммы скидки
							$('.amount-items > span:nth-child(2), .total-price').text('$' + (Number(currentAmountPrice) + Number(discVal)).toFixed(2)); //обновление общей стоимости товаров
						}
						//отменена карта
						if ($(currentForm).attr('id') === 'present-card-form') {
							var cardAmount = Number(response['card_amount']);
							restDisc = (Number($('.discounts-total > .discount-value').text().trim().slice(2)) - cardAmount).toFixed(2);
							$('.discounts-total > .discount-value').text('-$' + restDisc); //обновления суммы скидки
							$('.amount-items > span:nth-child(2), .total-price').text('$' + (Number(currentAmountPrice) + cardAmount).toFixed(2)); //обновление общей стоимости товаров

						}
						if (restDisc === '0.00') {
							$('.block-totals').find('.discounts-total, .without-discounts').remove(); //удаление блока с информацией о суммах скидок
						}

						$(currentForm).find('.material-symbols-outlined').remove(); //удаление значка
					}
				}

			},
			error: function(jqXHR, textStatus, errorThrown) {
				//переход на страницу для входа в систему, если статус ответа 401
				if(errorThrown === 'Unauthorized') {
					var login_url = jqXHR.responseJSON['login_page_url'];
					window.open(login_url, '_self');
				}
				
			},
		})
	}); 
})