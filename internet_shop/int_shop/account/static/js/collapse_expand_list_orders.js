$(document).ready(function() {
    $('.show-all-orders, .hide-another-orders').click(function() {
        var collapseOrders = $('.collapse-order'); //all blocks, that should be hidden

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