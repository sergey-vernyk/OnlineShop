$(document).ready(function() {
	var listInputs = $('[id^=id_code]'); //all inputs in a block
	var initialCurrentAmountPrice = Number($('.amount-items > span:nth-child(2)').text().slice(1)).toFixed(2);

	//make buttons for confirm form inactive and with another color
	for (var i = 0; i < listInputs.length; i++) {
		if (!$(listInputs[i]).val()) {
			$(listInputs[i]).closest('form').find('button').css({
				'pointer-events': 'none',
				'background-color': '#BFC0C0',
				'color': '#DCDFE1'
			});
		};
	}

	//tracking typing into each input field
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

	//tracking submitting form for code
	$('#coupon-form, #present-card-form').on('submit', function(event) {
		event.preventDefault();
		var currentForm = $(this);
		var submitBtn = $(this).find(':submit');
		var action = $(currentForm).find('input[name=action]').val(); //action is taken from the hidden field with name `action`
		var url;
		var boundErrorList = $(this).parent().find('.errorlist'); //errors list, linked with selected form

		//applying coupon/present card or their canceling
		if (action === 'Apply') {
			url = $(this).data('url-apply');
		} else if (action === 'Cancel') {
			url = $(this).data('url-cancel');
		}
		var code = $(this).find(':text').val(); //coupon/present card code
		var token = $(this).find(':hidden').val();

		$.ajax({
			url: url,
			method: 'POST',
			data: {
				code: code,
				csrfmiddlewaretoken: token,
			},
			success: function(response) {
				//list of all prices of products in the cart
				var allProductsPrices = $('.item-price').map(function() {
					return Number($(this).text().trim().slice(1));
				}).get();

				//sum of all these prices
				var totalPriceWithoutDiscounts = allProductsPrices.reduce(function(x, y) {
					return x + y;
				});

				//current cost of all products with all discounts
				var currentAmountPrice;
				if($('.amount-items > span:nth-child(2)').text() === django.gettext('Free')) {
					currentAmountPrice = initialCurrentAmountPrice;
				} else {
					currentAmountPrice = Number($('.amount-items > span:nth-child(2)').text().slice(1)).toFixed(2)
				}

				var finallyPriceWithCoupon = 0;
				var finallyPriceWithCard = 0;
				var formErrors = response['form_errors'];
				//if there are errors in the form
				if (formErrors) {
					var error = formErrors['code'][0];
					//if no errors have been displayed yet
					if(!boundErrorList.has('li').length) {
					    //adding error into error list in template
					    $(boundErrorList).prepend(`<li style="text-align: left;">${error}</li>`);
					}
				} else {
					$(boundErrorList).find('li').remove(); //deleting list item, that with error
                    //applying discounts
					if (action === 'Apply') {
						submitBtn.text(django.gettext('Cancel'));
						$(currentForm).find('input[name=action]').val('Cancel')
						//coupon has been applied
						if ($(currentForm).attr('id') === 'coupon-form') {
							var couponDiscount = response['coupon_discount'];
							finallyPriceWithCoupon = totalPriceWithoutDiscounts - (totalPriceWithoutDiscounts * Number(couponDiscount)).toFixed(2);
							initialCurrentAmountPrice = finallyPriceWithCoupon;
							$('.amount-items > span:nth-child(2), .total-price').text('$' + finallyPriceWithCoupon.toFixed(2));
						}
						//present card has been applied
						if ($(currentForm).attr('id') === 'present-card-form') {
							var cardAmount = response['card_amount'];
							finallyPriceWithCard = currentAmountPrice - Number(cardAmount);
							initialCurrentAmountPrice = finallyPriceWithCard;
							$('.amount-items > span:nth-child(2), .total-price').text(finallyPriceWithCard > 0 ? `$${finallyPriceWithCard.toFixed(2)}` : django.gettext('Free'));
						}

						//content appear, when one of discounts was applied
						var contentSummary = `<div class="discounts-total">
                                                  <div class="discount-title">${django.gettext('Amount discounts:')}</div>
                                                  <div class="discount-value">-$${(currentAmountPrice - (finallyPriceWithCoupon || finallyPriceWithCard)).toFixed(2)}</div>
                                              </div>
                                              <div class="without-discounts">
                                                  <div class="without-title">${django.gettext('Without discounts:')}</div>
                                                  <div class="without-value">$${currentAmountPrice}</div>
                                              </div>`

						//paste icon about successfully applying coupon or present card
						$(currentForm).append('<span class="material-symbols-outlined">check_circle</span>');

						//if was applied one of discounts
						if (!$('.block-totals').children('.discounts-total, .without-discounts').length) {
							$('.block-summary').after(contentSummary); //adding to the bottom of the block information about discount amount and cost without discount

							//if the second discount was present card
						} else if (finallyPriceWithCard) {
							var curDiscVal = Number($('.discount-value').text().slice(2)); //current discount value
							var finallyDiscVal = (curDiscVal + Number(cardAmount)).toFixed(2) //finally discount value
							$('.discounts-total > .discount-value').replaceWith(
								`<div class="discount-value">
                                    -$${finallyDiscVal}
                                </div>`
							);

							//if second discount was coupon
						} else if (finallyPriceWithCoupon) {
							var curDiscVal = Number($('.discount-value').text().slice(2)); //current discount value
							var finallyDiscVal = (curDiscVal + (totalPriceWithoutDiscounts * Number(couponDiscount))).toFixed(2); //finally discount value
							$('.discounts-total > .discount-value').replaceWith(
								`<div class="discount-value">
                                    -$${finallyDiscVal}
                                </div>`
							);
							//finally cost with discounts in the top of the block
							$('.amount-items > span:nth-child(2)').text('$' + (totalPriceWithoutDiscounts - finallyDiscVal))
						}

					} else if (action === 'Cancel') {
						submitBtn.text(django.gettext('Apply'));
						$(currentForm).find('input[name=action]').val('Apply')
						var restDisc; //remaining sum of discount
						//coupon was canceled
						if ($(currentForm).attr('id') === 'coupon-form') {
							var discVal = Number(totalPriceWithoutDiscounts * response['coupon_discount']).toFixed(2);
							restDisc = (Number($('.discounts-total > .discount-value').text().trim().slice(2)) - discVal).toFixed(2);
							$('.discounts-total > .discount-value').text('-$' + restDisc); //updated sum of discount
							$('.amount-items > span:nth-child(2), .total-price').text('$' + (Number(currentAmountPrice) + Number(discVal)).toFixed(2)); //updating total cost of goods
						}
						//present cart was canceled
						if ($(currentForm).attr('id') === 'present-card-form') {
							var cardAmount = Number(response['card_amount']);
							restDisc = (Number($('.discounts-total > .discount-value').text().trim().slice(2)) - cardAmount).toFixed(2);
							$('.discounts-total > .discount-value').text('-$' + restDisc); //updating sum of discount
							$('.amount-items > span:nth-child(2), .total-price').text('$' + (Number(currentAmountPrice) + cardAmount).toFixed(2)); //updating total cost of goods

						}
						if (restDisc === '0.00') {
							$('.block-totals').find('.discounts-total, .without-discounts').remove(); //deleting block with information about discount sums
						}

						$(currentForm).find('.material-symbols-outlined').remove(); //deleting icon
					}
				}

			},
			error: function(jqXHR, textStatus, errorThrown) {
				//redirecting to the login page, when response status is 401
				if(errorThrown === 'Unauthorized') {
					var login_url = jqXHR.responseJSON['login_page_url'];
					window.open(login_url, '_self');
				}
				
			},
		})
	}); 
})