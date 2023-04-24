$(document).ready(function(){
    CheckForHighlight();
});

function CheckForHighlight(){
    var href = window.location.href;
    var values = href.split('?')[1]; //взятие значения после '?'
    var order_id = values.split('=')[1].split('-')[1]; //получение номера заказа
    //поиск родительского класса с информацией о заказе и добавление класса к нему
    $(`#total-cost-${order_id}`).parentsUntil('.row p-0 border rounded mb-2').first().addClass('highlighted-element');
}