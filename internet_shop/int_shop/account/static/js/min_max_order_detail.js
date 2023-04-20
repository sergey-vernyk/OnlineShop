$(document).ready(function() {
    $('[id^=order-detail]').hide();
    $('[id^=expander]').click(function(){
        var order_id = this.id.slice(9); //достаем id заказа из нажатой кнопки
        var currentAttr = $(this).find('img').attr('src'); //получение значения пути к иконке
        var src = replaceIconPath(currentAttr, order_id);
        $(`#expander-${order_id} > img`).attr('src', src);
        $(`#order-detail-${order_id}`).slideToggle();
    });

    function replaceIconPath(src, order_id) {
        var addrParts = src.split('/');  //делим адрес по '/'
        var indexLast = addrParts.length - 1;  //поиск индекса с названием иконки
        var last = addrParts[indexLast]; //получение названия текущей иконки

        //установка имени нужной иконки
        if(last === 'chevron-down.svg') {
            addrParts[indexLast] = 'chevron-up.svg';
            $(`#total-cost-${order_id}, #items-images-${order_id}`).hide();
            $('.expander-header').css('border-bottom', '1px solid #ced4da');
        } else {
            addrParts[indexLast] = 'chevron-down.svg';
            $(`#total-cost-${order_id}, #items-images-${order_id}`).show();
            $('.expander-header').css('border-bottom', '0px solid #ced4da');
        }

        var src = addrParts.join('/'); //создание нового адреса

        return src;
    }
})
