import getCookie from '/static/js/getCSRFToken.js';

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
                var cartLength = response['cart_len']
                //set quantity products value and their total cost in the cart
                $('.amount-cart').text(cartLength);
                $('.amount-items > div:nth-child(1) > span:nth-child(1)').text(cartLength);
                var totalPrice = response['total_price'];
                var totalPriceDiscount = response['total_price_discounts'];
                var totalDiscount = response['total_discount'];
                //if all goods were deleted from the cart
                if(!cartLength) {
                     $('.total-price').text('');
                     $('.block-totals').remove();
                     //added picture with text `your cart is empty` on current language
                     $('.block-cart-items').parent().prepend(get_pic_for_empty_cart(response['language'])); 
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
    /**
     * 
     * @param {string} language current language
     * @returns {string} string with image's src which linked to current language
     */
    function get_pic_for_empty_cart(language) {
        const emptyCartPic = `<div class="empty-cart">
                                <img src="/static/img/your-cart-is-empty_${language}.png" width="350" height="350">
                            </div>`
        return emptyCartPic
    }
});