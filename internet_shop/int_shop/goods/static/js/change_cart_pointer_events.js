$(document).ready(function() {
    var currentCartAmount = Number($('.amount-cart').text().trim());

    //отключения перехода в корзину, когда в ней нет добавленных товаров
    if(currentCartAmount) {
        $('.cart-button').css('pointer-events', 'all');
    } else {
        $('.cart-button').css('pointer-events', 'none');
    }
})