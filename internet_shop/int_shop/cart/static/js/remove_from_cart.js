import getCookie from '/static/js/getCSRFToken.js';

const emptyCartPic = `<div class="empty-cart">
                          <img src="/static/img/your-cart-is-empty.png" width="350" height="350">
                      </div>`

$(document).ready(function() {
    $('.cart-remove').click(function(event) {
        event.preventDefault();
        var url = $(this).data('url');
        var product_card = $(this).parentsUntil('.block-cart-items').last() //product card in the cart
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
                //set quantity products value and their total cost in the cart
                $('.amount-cart').text(response['cart_len']);
                $('.amount-items > div:nth-child(1) > span:nth-child(1)').text(response['cart_len']);
                var totalPrice = response['total_price'];
                var totalPriceDiscount = response['total_price_discounts'];
                var totalDiscount = response['total_discount'];
                //if all goods were deleted from the cart
                if(totalPrice === 0 ) {
                     $('.total-price').text('');
                     $('.block-totals').remove();
                     $('.block-cart-items').parent().prepend(emptyCartPic);  //added picture with text "your cart is empty"
                     $('.block-cart-items').remove();
                } else {
                    $('.total-price, .amount-items > span:nth-child(2)').text(totalPriceDiscount > 0 ? `$${totalPriceDiscount}` : 'Free');
                    $('.discounts-total > .discount-value').text('-$' + totalDiscount);
                    $('.without-discounts > .without-value').text('$' + totalPrice);
                }

                product_card.remove();  //deleting product card
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            },

        })

    })

});