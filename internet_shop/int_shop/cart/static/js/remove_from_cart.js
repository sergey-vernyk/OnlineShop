import getCookie from '/static/js/getCSRFToken.js';

$(document).ready(function() {
    $('.cart-remove').click(function(event) {
        event.preventDefault();
        var url = $(this).data('url');
        var product_card = $(this).parentsUntil('.block-cart-items').last() //карточка товара в корзине
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
                //установка значений кол-ва товаров в корзине и их общей стоимости
                $('.amount-cart').text(response['cart_len']);
                $('.amount-items > div:nth-child(1) > span:nth-child(1)').text(response['cart_len']);
                var totalPrice = response['total_price'];
                var totalPriceDiscount = response['total_price_discounts'];
                var totalDiscount = response['total_discount'];
                //если все товары были удалены из корзины
                if(totalPrice === 0 ) {
                     $('.total-price').text('');
                     $('.block-cart-items').remove();  //удаление блока без карточек товаров
                     $('.block-totals').remove();
                     //переход на предыдущую страницу, с которой был переход в корзину
                     window.open(response['prev_url'], '_self');
                } else {
                    $('.total-price, .amount-items > span:nth-child(2)').text(totalPriceDiscount > 0 ? `$${totalPriceDiscount}` : 'Free');
                    $('.discounts-total > .discount-value').text('-$' + totalDiscount);
                    $('.without-discounts > .without-value').text('$' + totalPrice);
                }

                product_card.remove();  //удаление карточки товара
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            },

        })

    })

});