$(document).ready(function() {
    $('[id^=id_quantity]').change(function() {
        var parentForm = $(this).parentsUntil('.item-quantity').last(); //search for the form in which value was changed
        var url = parentForm.data('url');
        var token = parentForm.find('input[name=csrfmiddlewaretoken]').val();
        var product_id = parentForm.attr('id').split('-')[2];
        var quantity = $(this).val(); //quantity value from the form

        $.ajax({
            url: url,
            method: 'POST',
            dataType: 'json',
            data: {
                csrfmiddlewaretoken: token,
                product_id: product_id,
                quantity: quantity,
            },
            success: function(response) {
                //searching the block with product card, in which quantity was changed
                var currentProductCart = parentForm.closest('.cart-item').find('.item-price');
                var currentProductCost = response['added_prod_cost']; //current product cost after changing quantity
                var currentProductsInCart = response['cart_len'];
                var totalPriceDiscounts = response['total_price_discounts'];
                const isPluralAmount = currentProductsInCart === 1 ? false : true; //plural or singular products quantity

                $('.amount-cart').text(currentProductsInCart); //amount quantity of goods in the cart
                $('.amount-items > div:nth-child(1) > span:nth-child(2)').text(isPluralAmount ? 'products': 'product');
                $('.total-price').text(totalPriceDiscounts > 0 ? `$${totalPriceDiscounts}`: 'Free'); //the final cost of goods in header
                currentProductCart.text('$' + currentProductCost);
                $('.amount-items > div:nth-child(1) > span:nth-child(1)').text(response['cart_len']);
                $('.amount-items > span:nth-child(2)').text(totalPriceDiscounts > 0 ? `$${totalPriceDiscounts}`: 'Free');
                $('.discount-value').text('-$' + response['total_discount']); //total discount amount
                $('.without-value').text('$' + response['total_price']); //amount cost of goods without discount
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);

            },
        })
    })
})