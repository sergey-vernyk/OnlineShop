$(document).ready(function() {

	const allStars = $('.rating-star').children();

	//функция возвращает текущие статусы звезд рейтинга товара в виде словаря
	function getStarsStatus(objects) {
		var statuses = {};
		objects.map(function() {
			return statuses[$(this).attr('id')] = $(this).hasClass('checked');
		}).get();
		return statuses;
	}

	const currentStarsStatus = getStarsStatus(allStars); //текущее состояние звезд рейтинга

	$('[id^=star-]').on('click mouseenter mouseleave', function(event) {
		const starId = $(this).attr('id').slice(5); //звезда, над которой произошло событие

		switch (event.type) {
			case 'click':
				var token = $('#rating-form').find('input[name=csrfmiddlewaretoken]').val();
				var productId = $('#rating-form').data('pk');
				var url = $('#rating-form').data('url');

				$.post(
					url, {
						star: starId,
						product_id: productId,
						csrfmiddlewaretoken: token
					},
					function(response) {
						var rating = Number(response['current_rating']); //получение текущего установленного рейтинга с view
                        $('.current-rating-digits').text(rating.toFixed(1));
                        
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

			case 'mouseenter': //наведение курсора на звезду
				for (var i = Number(starId); i > 0; i--) {
                    //если звезда еще не была закрашена - закрасить ее и все звезды перед ней
					if (!$(`#star-${i}`).hasClass('checked'))
						$(`#star-${i}`).addClass('checked');
				}
				break;

			case 'mouseleave': //отведение курсора от звезды
				for (var i = Number(starId); i > 0; i--) {
                    /*если звезда была закрашена при наведении и не была закрашена
                     до наведения курсора - убрать ее закрашивание и звезд до нее*/
					if ($(`#star-${i}`).hasClass('checked') && !currentStarsStatus[$(`#star-${i}`).attr('id')])
						$(`#star-${i}`).removeClass('checked');
				}
				break;

			default:
				break;
		}
	})
});