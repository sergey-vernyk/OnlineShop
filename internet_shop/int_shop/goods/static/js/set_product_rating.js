$(document).ready(function() {
    var star;
    //поиск значения выбранной оценки
    checkSelect = function() {
        star = $('#star_id').find(':selected').val();
    };
    //подтверждение формы при выборе оценки товара
    formSubmit = function(url, product_id) {
        var token = $('#rating-form').find('input[name=csrfmiddlewaretoken]').val();
        $.ajax({
            url: url,
            method: 'POST',
            data: {
                star: star,
                product_id: product_id,
                csrfmiddlewaretoken: token,
            },
            //"закрашивание" звезд рейтинга в зависимости от рейтинга товара
            success: function(response, status) {
                var rating = response['current_rating']; //получение текущего установленного рейтинга с view
                if (rating == 1) {
                    for (var i = 2; i < 6; i++)
                        if ($(`#star-${i}`).hasClass('checked'))
                            $(`#star-${i}`).removeClass('checked');

                    $(`#star-${rating}`).addClass('checked');
                } else if (rating == 2) {
                    for (var i = 3; i < 6; i++)
                        if ($(`#star-${i}`).hasClass('checked'))
                            $(`#star-${i}`).removeClass('checked');

                    for (var i = 1; i < 3; i++)
                        $(`#star-${i}`).addClass('checked');
                } else if (rating == 3) {
                    for (var i = 3; i < 6; i++)
                        if ($(`#star-${i}`).hasClass('checked'))
                            $(`#star-${i}`).removeClass('checked');

                    for (var i = 1; i < 4; i++)
                        $(`#star-${i}`).addClass('checked');

                } else if (rating == 4) {
                    for (var i = 4; i < 6; i++)
                        if ($(`#star-${i}`).hasClass('checked'))
                            $(`#star-${i}`).removeClass('checked');

                    for (var i = 1; i < 5; i++)
                        $(`#star-${i}`).addClass('checked');
                } else if (rating = 5)

                    for (var i = 1; i < 6; i++)
                        $(`#star-${i}`).addClass('checked');
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            }

        })
    };
});