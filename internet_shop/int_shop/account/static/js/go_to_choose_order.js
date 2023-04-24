$(document).ready(function(){
    $('.go-order').click(function(event){
        event.preventDefault();
        var sel = $('[id^=coupon-]').find(':selected').val(); //поиск выбранного пункта
        var order_id = $('[id^=coupon-]').find(':selected').html().split(' ')[1]; //номер заказа
        var url = $(this).data('url');
        window.open(`${url}?highlight=order-${order_id}`, '_self'); //адрес для подсветки выбранного заказа
    });
})

