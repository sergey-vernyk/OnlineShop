$ = django.jQuery;

//show or hide field with promotional price while activating or deactivating checkbox on the Promotional field
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