import getCookie from '/static/js/getCSRFToken.js';

$(document).ready(function() {
    // handling click on the captcha image
    $('.captcha-image > img').click(function() {
        var url = $(this).data('url');
        // user email as identifier for storing captcha text
        var userEmail = $('.reg-form-fields').find('input[name=email]').val();
        const witdh = 200;
        const height = 60;
        const fontSize = 30;
        const csrftoken = getCookie('csrftoken');

        $.ajax({
            url: url,
            method: 'POST',
            dataType: 'json',
            data: {
                width: witdh,
                height: height,
                font_size: fontSize,
                user_email: userEmail,
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