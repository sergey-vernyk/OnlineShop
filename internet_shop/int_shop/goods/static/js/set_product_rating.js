$(document).ready(function() {

	const allStars = $('.rating-star').children();
	var was_click = false;
	var currentStarsStatus = undefined;

	//function returns current statuses of rating stars of a product in a dictionary form
	function getStarsStatus(objects) {
		var statuses = {};
		objects.map(function() {
			return statuses[$(this).attr('id')] = $(this).hasClass('checked');
		}).get();
		return statuses;
	}

	currentStarsStatus = getStarsStatus(allStars); //current state of rating stars

	$('[id^=star-]').on('click mouseenter mouseleave', function(event) {
		const starId = $(this).attr('id').slice(5); //the star, on which the event occurred

		switch (event.type) {
			case 'click':
				var token = $('#rating-form').find('input[name=csrfmiddlewaretoken]').val();
				var productId = $('#rating-form').data('pk');
				var url = $('#rating-form').data('url');
				was_click = true;

				$.post(
					url, {
						star: starId,
						product_id: productId,
						csrfmiddlewaretoken: token
					},
					function(response) {
						var rating = Number(response['current_rating']); //getting current set rating from view
                        $('.current-rating-digits').text(`( ${rating.toFixed(1)} )`);
                        
                        switch (Math.round(rating)) {
                            case 1:
                                for (var i = 2; i < 6; i++)
								    if ($(`#star-${i}`).hasClass('checked'))
									    $(`#star-${i}`).removeClass('checked');

							    $(`#star-${rating}`).addClass('checked');
                                break;

                            case 2:
                                for (var i = 3; i < 6; i++)
                                    if ($(`#star-${i}`).hasClass('checked'))
                                        $(`#star-${i}`).removeClass('checked');

                                for (var i = 1; i < 3; i++)
                                    $(`#star-${i}`).addClass('checked');

                                break;

                            case 3:
                                for (var i = 3; i < 6; i++)
                                    if ($(`#star-${i}`).hasClass('checked'))
                                        $(`#star-${i}`).removeClass('checked');

							    for (var i = 1; i < 4; i++)
								    $(`#star-${i}`).addClass('checked');

                                break;
                            
                            case 4:
                                for (var i = 4; i < 6; i++)
                                    if ($(`#star-${i}`).hasClass('checked'))
                                        $(`#star-${i}`).removeClass('checked');

                                for (var i = 1; i < 5; i++)
                                    $(`#star-${i}`).addClass('checked');

                                break;

                            case 5:
                                for (var i = 1; i < 6; i++)
								    $(`#star-${i}`).addClass('checked');

                                break;
                        
                            default:
                                break;
                        }
					},
					'json',
				)
				break;

			case 'mouseenter': //hovering cursor above the star
				for (var i = Number(starId); i > 0; i--) {
                    //if the star aren't colored - will color it and all stars before it
					if (!$(`#star-${i}`).hasClass('checked'))
						$(`#star-${i}`).addClass('checked');
				}
				break;

			case 'mouseleave': //moving the cursor away from the star
				if (!was_click) {
					for (var i = Number(starId); i > 0; i--) {
                    /*if star were colored while hovering and weren't colored before hovering -
                    will remove it color and color of the all stars before it*/
					if ($(`#star-${i}`).hasClass('checked') && !currentStarsStatus[$(`#star-${i}`).attr('id')])
						$(`#star-${i}`).removeClass('checked');
				}
				} else {
					currentStarsStatus = getStarsStatus(allStars);
					for(var i = 1; i < 6; i++) {
						if(currentStarsStatus[`star-${i}`] === true) {
							$(`#star-${i}`).addClass('checked');
						}
					}
					was_click = false;
				}
				break;

			default:
				break;
		}
	})
});