$(document).ready(function(){
    CheckForHighlight();
});

function CheckForHighlight(){
    var href = window.location.href;
    var values = href.split('?')[1]; //value after "?"
    if(values) {
        var order_id = values.split('=')[1].split('-')[1]; //getting order number
        //searching parents class with an the order information and adding class to it
        $(`#total-cost-${order_id}`).parentsUntil('.row p-0 border rounded mb-2').first().addClass('highlighted-element');
    }
}