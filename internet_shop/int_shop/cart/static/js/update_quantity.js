$(document).ready(function() {
    $('[id^=id_quantity]').change(function() {
        var parentForm = $(this).parentsUntil('.item-quantity').last(); //поиск формы, в которой изменилось значение
        var url = parentForm.data('url');
        var token = parentForm.find('input[name=csrfmiddlewaretoken]').val();
        var product_id = parentForm.attr('id').split('-')[2];
        var quantity = $(this).val(); //значение кол-ва из формы

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
                //поиск блока с карточкой товара, в котором изменилось кол-во
                var currentProductCart = parentForm.closest('.cart-item').find('.item-price');
                var currentProductCost = response['added_prod_cost']; //текущая стоимость товара после изменения кол-ва
                var currentProductsInCart = response['cart_len'];
                var totalPriceDiscounts = response['total_price_discounts'];
                const isPluralAmount = currentProductsInCart === 1 ? false : true; //множественное или единичное кол-во товаров

                $('.amount-cart').text(currentProductsInCart); //кол-во товара в корзине
                $('.amount-items > div:nth-child(1) > span:nth-child(2)').text(isPluralAmount ? 'products': 'product');
                $('.total-price').text(totalPriceDiscounts > 0 ? `$${totalPriceDiscounts}`: 'Free'); //окончательная цена товаров в header
                currentProductCart.text('$' + currentProductCost);
                $('.amount-items > div:nth-child(1) > span:nth-child(1)').text(response['cart_len']);
                $('.amount-items > span:nth-child(2)').text(totalPriceDiscounts > 0 ? `$${totalPriceDiscounts}`: 'Free');
                $('.discount-value').text('-$' + response['total_discount']); //общая сумма скидки
                $('.without-value').text('$' + response['total_price']); //общая стоимость товаров без скидки
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);

            },
        })
    })
})