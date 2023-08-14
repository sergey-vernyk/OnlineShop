$(document).ready(function() {
	var statuses = getStatusDiscounts(); //applied discounts statuses
    /*show (hide) form and activate(deactivate) checkbox while page is loading,
    when coupon(present card) was applied(canceled)*/
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
	    //checking, whether selected whatever checkbox
		switch (this.checked) {
			case true:
				if ($(this).attr('id').endsWith('coupon')) {
					$('#coupon-form').show();
					$('#have-card').prop('disabled', true);
				} else if ($(this).attr('id').endsWith('card')) {
					$('#present-card-form').show();
					$('#have-coupon').prop('disabled', true);
				}
				$(this).parent().nextAll().filter('.errorlist').eq(0).show(); //displaying errors near the form
				break;

			case false:
				if ($(this).attr('id').endsWith('coupon')) {
					$('#coupon-form').hide();
					$('#have-card').prop('disabled', false);
				} else if ($(this).attr('id').endsWith('card')) {
					$('#present-card-form').hide();
					$('#have-coupon').prop('disabled', false);
				}
				$(this).parent().nextAll().filter('.errorlist').eq(0).hide(); //hiding errors near the form
				break;
		}
	})
	//getting statuses for apply/cancel coupon or present card buttons
	function getStatusDiscounts() {
		var dict = {};
		const statuses = $('.coupon-btn, .present-card-btn').map(function() {
			return dict[$(this).attr('class')] = $(this).text().trim();
		}).get();

		return dict;
	}
})