$(document).ready(function() {
    var order;
    checkSelect = function() {
        // поиск выбранного пункта
        order = $('#order_id').find(':selected').val();
    };

    formSubmit = function() {
        // подтверждение формы
        $('#sorting-form').submit();
    };
});