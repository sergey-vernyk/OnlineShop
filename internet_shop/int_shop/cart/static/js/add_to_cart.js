$(document).ready(function() {
    var currentCartLen;
    //selector select button with id, which starts on "add-to-cart"
    $('[id^=add-to-cart]').click(function(event) {
        var product_id = this.id.slice(12); //get product id from button that was pressed
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
                //set quantity products in cart and their total cost
                $('.amount-cart').text(response['cart_len']);
                $('.total-price').text('$' + response['total_price']);
                $('.cart-button').css('pointer-events', 'all'); //enable the ability to go to the cart
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
                
            },

        })

    })
    // returns value from dict by the specified key
    function getValue(data, value) {
        values = {};
        // getting value from data and create new dict
        data.forEach(function(element) {
            values[element.name] = element.value;
        });
        return values[value];
    }

});