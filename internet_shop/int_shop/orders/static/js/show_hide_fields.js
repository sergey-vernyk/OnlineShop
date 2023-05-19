$(document).ready(function() {
    var methodInput = $(':input[id=id_delivery_form-method]'); //поле для выбора метода доставки заказа

    var addressInput = $('#id_order_form-address'); //поле ввода адреса доставки
    var officeNumberInput = $('#id_delivery_form-office_number'); //поле для выбора номера отделения доставки
    //изменение видимости номера отделения в зависимости от метода
    changeVisibility($(methodInput).find(':selected').val());

    $(methodInput).change(function() {
        var sel = $(this).find(':selected').val();
        changeVisibility(sel);
    });

    //функция изменят видимость поля ввода в зависимости от значения inputVal
    function changeVisibility(inputVal) {
        if(inputVal === 'Post office') {
            $(officeNumberInput).parent('.order-form-fields').show();
        } else if(inputVal === 'Self-delivery' || inputVal === 'Apartment' || inputVal === '') {
            $(officeNumberInput).parent('.order-form-fields').hide();
        }

        if(inputVal === 'Apartment') {
            $(addressInput).parent('.order-form-fields').show();
            $(addressInput).focus(); //установить курсор на поле адреса
        } else if(inputVal === 'Post office' || inputVal === '' || inputVal === 'Self-delivery')
            $(addressInput).parent('.order-form-fields').hide();
    }
})