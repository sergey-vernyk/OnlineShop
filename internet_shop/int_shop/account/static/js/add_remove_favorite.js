import getCookie from '/static/js/getCSRFToken.js';

$(document).ready(function() {
    $('[id^=remove-fav], #add-rem-fav').click(function() {
        var product_id;
        var action;
        //определение кнопки, которая была нажата (удалить или добавить)
        if ($(this).attr('id').startsWith('add-')) {
            product_id = $(this).data('pk');
            action = getAction($(this).text());
        } else if ($(this).attr('id').startsWith('remove-')) {
            product_id = this.id.slice(11); //получение id товара
            action = $(this).data('action');
        }

        var url = $(this).data('url');
        const csrftoken = getCookie('csrftoken');

        $.ajax({
            url: url,
            method: 'POST',
            dataType: 'json',
            data: {
                action: action,
                product_id: product_id,
                csrfmiddlewaretoken: csrftoken,
            },

            success: function(response) {
                var amount_prods = response['amount_prods']; //текущее кол-во товаров в избранном
                if (action === 'remove') {
                    $(`#fav-prod-${product_id}`).remove(); //удаление блока с товаром из избранного
                    //отображение текущего кол-ва товаров в header
                    $('.often-use-menu > ul:nth-child(2) > li:nth-child(2) > span:nth-child(1) > a:nth-child(1)').text(amount_prods);
                    if (amount_prods === 0) {
                        //если нет больше товаров в избранном
                        $('.personal-info').append(`<div class="empty-customer-content">
                                                    <h4 class="d-inline">There are no favorite products yet...</h4>
                                                    </div>`);
                    }
                    $('#add-rem-fav').text('Add to Favorite'); // изменить надпись на кнопке
                } else if (action === 'add') {
                    $('#add-rem-fav').text('Remove from Favorite');
                }
            },

            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            },
        })
        //функция возвращает нужное действие, которое находится в тексте кнопки
        function getAction(text) {
            return text.split(' ')[0].toLowerCase();
        }
    });
})