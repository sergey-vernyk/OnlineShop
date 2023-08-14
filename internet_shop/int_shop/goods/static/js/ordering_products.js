$(document).ready(function() {
    var order;
    checkSelect = function() {
        //searching selected item
        order = $('#order_id').find(':selected').val();
    };

    formSubmit = function() {
        //submitting form
        $('#sorting-form').submit();
    };
});