$(document).ready(function(){
    $('.go-order').click(function(event){
        event.preventDefault();
        var sel = $('[id^=coupon-]').find(':selected').val(); //searching selected item
        var order_id = $('[id^=coupon-]').find(':selected').html().split(' ')[1]; //order number
        var url = $(this).data('url');
        window.open(`${url}?highlight=order-${order_id}`, '_self'); //address for backlight selected order
    });
})

