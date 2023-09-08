import getCookie from '/static/js/getCSRFToken.js';

$(document).ready(function() {
    // handling click on the captcha image
    $('.captcha-image > img').click(function() {
        const url = $(this).data('url');
        const width = $(this).data('width') || 200;
        const height = $(this).data('height') || 60;
        const fontSize = $(this).data('fontSize') || 30;

        const csrftoken = getCookie('csrftoken');

        $.ajax({
            url: url,
            method: 'POST',
            dataType: 'json',
            data: {
                width: width,
                height: height,
                font_size: fontSize,
                csrfmiddlewaretoken: csrftoken,
            },
            success: function(response) {
                // update captcha image itself
                $('.captcha-image > img').attr('src', `data:image/png;base64,${response.captcha_image}`)
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            }
        })
    })
})