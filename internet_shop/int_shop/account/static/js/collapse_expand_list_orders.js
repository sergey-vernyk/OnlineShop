$(document).ready(function() {
    $('.show-all-orders, .hide-another-orders').click(function() {
        var collapseOrders = $('.collapse-order'); //все блоки, которые должны быть скрыты

        if(collapseOrders && $(collapseOrders).is(':hidden')) {
            $(collapseOrders).slideDown(500);
            $('.show-all-orders').hide();
            $('.hide-another-orders').css({'display': 'inline'}).show();
        } else {
            $(collapseOrders).slideUp(500);
            $('.show-all-orders').show();
            $('.hide-another-orders').hide();
        }
    })
})