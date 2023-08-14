$(document).ready(function() {
    var methodInput = $(':input[id=id_delivery_form-method]'); //field for select delivery method for an order

    var addressInput = $('#id_order_form-address'); //field for enter delivery address
    var officeNumberInput = $('#id_delivery_form-office_number'); //field for select office number of delivery
    //changing visibility delivery office number depending on delivery method
    changeVisibility($(methodInput).find(':selected').val());

    $(methodInput).change(function() {
        var sel = $(this).find(':selected').val();
        changeVisibility(sel);
    });

    //function changes field visibility depending on inputVal value
    function changeVisibility(inputVal) {
        if(inputVal === 'Post office') {
            $(officeNumberInput).parent('.order-form-fields').show();
        } else if(inputVal === 'Self-delivery' || inputVal === 'Apartment' || inputVal === '') {
            $(officeNumberInput).parent('.order-form-fields').hide();
        }

        if(inputVal === 'Apartment') {
            $(addressInput).parent('.order-form-fields').show();
            $(addressInput).focus(); //set cursor om the field
        } else if(inputVal === 'Post office' || inputVal === '' || inputVal === 'Self-delivery')
            $(addressInput).parent('.order-form-fields').hide();
    }
})