import getCookie from '/static/js/getCSRFToken.js';

var addIcon = `<svg xmlns="http://www.w3.org/2000/svg"
                   width="25" height="25" fill="currentColor" class="bi bi-heart-fill" viewBox="0 0 16 16">
                   <path fill-rule="evenodd" d="M8 1.314C12.438-3.248 23.534 4.735 8 15-7.534 4.736 3.562-3.248 8 1.314z"/>
               </svg>`

var removeIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" fill="currentColor"
                        class="bi bi-heart" viewBox="0 0 16 16">
                        <path d="m8 2.748-.717-.737C5.6.281 2.514.878 1.4 3.053c-.523
                        1.023-.641 2.5.314 4.385.92 1.815 2.834 3.989 6.286 6.357
                        3.452-2.368 5.365-4.542 6.286-6.357.955-1.886.838-3.362.314-4.385C13.486.878
                        10.4.28 8.717 2.01L8 2.748zM8 15C-7.333 4.868 3.279-3.04 7.824
                        1.143c.06.055.119.112.176.171a3.12 3.12 0 0 1 .176-.17C12.72-3.042 23.333 4.867 8 15z"/>
                  </svg>`

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
                var amount_prods = response['amount_prods']; //текущее кол-во товаров в избранном\
                $('.add-to-favorite > svg').remove();
                if (action === 'remove') {
                    $('.add-to-favorite').prepend(removeIcon);
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
                    $('.add-to-favorite').prepend(addIcon);
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
