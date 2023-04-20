$(document).ready(function() {
    var currentCartLen;
    //селектор выбирает кнопку с id, который начинается на add-to-cart
    $('[id^=add-to-cart]').click(function(event) {
        var product_id = this.id.slice(12); //достаем id товара из нажатой кнопки
        event.preventDefault();
        event.stopPropagation();
        var data = $(`#add-form-${product_id}, #update-form-${product_id}`).serializeArray();
        var url = getValue(data, 'url');
        var token = getValue(data, 'csrfmiddlewaretoken');
        var quantity = getValue(data, 'quantity');

        $.ajax({
            url: url,
            method: 'POST',
            dataType: 'json',
            data: {
                product_id: product_id,
                quantity: quantity,
                csrfmiddlewaretoken: token,
                quantity: quantity,
            },
            success: function(response) {
                //установка значений кол-ва товаров в корзине и их общей стоимости
                $('.amount-cart').text(response['cart_len']);
                $('.total-price').text('$' + response['total_price']);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            },

        })

    })
    // возвращает значение из словаря по указанному ключу value
    function getValue(data, value) {
        values = {};
        // достает из data значения и делает новый словарь
        data.forEach(function(element) {
            values[element.name] = element.value;
        });
        return values[value];
    }

});