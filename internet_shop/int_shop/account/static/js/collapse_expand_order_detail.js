$(document).ready(function() {
    const expand = 'expand_more';
    const collapse = 'expand_less';

    $('[id^=expander]').click(function(){
        var order_id = this.id.slice(9); //getting order id from pressed button
        var currentSign = $(this).children();  //inner block with icon
        var currentAction = $(currentSign).text() == expand ? 'expand' : 'collapse';
        $(`#order-detail-${order_id}`).slideToggle();

        if(currentAction === 'expand') {
            $(currentSign).text(collapse);
            $(`#total-cost-${order_id}, #items-images-${order_id}`).hide();
            $(`#expander-${order_id}`).parent().css('border-bottom', '1px solid #ced4da');
        } else if(currentAction === 'collapse') {
            $(currentSign).text(expand);
            $(`#total-cost-${order_id}, #items-images-${order_id}`).show();
            $(`#expander-${order_id}`).parent().css('border-bottom', '0px solid #ced4da');
        }
    });
})
