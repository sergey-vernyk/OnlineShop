$ = django.jQuery;

/*скрытие или отображение поля для ввода акционной цены на товар
при активации или деактивации checkbox на поле Promotional*/
$(document).ready(function () {
    var promotionalField = $('.field-promotional').children().eq(0);
    var promotionalPriceField = $('.field-promotional_price');
    const checkbox = $(promotionalField).find(':input');

    if($(checkbox).prop('checked')) {
        $(promotionalPriceField).show()
    } else {
        $(promotionalPriceField).hide();
    }

    $(checkbox).click(function() {
        $(promotionalPriceField).toggle();
    })

})