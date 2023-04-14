import getCookie from '/static/js/getCSRFToken.js';

$(document).ready(function() {
    $('.cart-remove').click(function(event) {
        event.preventDefault();
        var url = $(this).attr('href');
        var parent = $(this).parentsUntil('.col-lg-7').last(); //карточка товара в корзине
        var product_id = $(this).data('pk');
        const csrftoken = getCookie('csrftoken');

        $.ajax({
            url: url,
            method: 'POST',
            dataType: 'json',
            data: {
                product_id: product_id,
                csrfmiddlewaretoken: csrftoken,
            },
            success: function(response) {
                console.log(response);
                //установка значений кол-ва товаров в корзине и их общей стоимости
                $('.amount-cart').text(response['cart_len']);
                var total_price = response['total_price']
                //если все товары были удалены из корзины
                if(total_price === '0.00' ) {
                     $('.total-price').text('');
                     $('.col-lg-7').remove();  //удаление блока без карточек товаров
                     $('.amount-items > span:nth-child(1)').text(0);  //установка кол-ва товаров в корзине равным нулю
                } else {
                    $('.total-price').text('$' + total_price);
                    parent.remove();  //удаление карточки товара
                }



            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            },

        })

    })

});