$(document).ready(function() {
    var currentCartAmount = Number($('.amount-cart').text().trim());

    //disable transition to the cart, when there are no added products in it
    if(currentCartAmount) {
        $('.cart-button').css('pointer-events', 'all');
    } else {
        $('.cart-button').css('pointer-events', 'none');
    }
})