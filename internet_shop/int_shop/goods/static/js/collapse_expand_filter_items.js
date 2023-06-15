$(document).ready(function() {

    //текст в значках
    const expandSign = 'expand_more';
    const collapseSign = 'expand_less';

    $('.title-filters > .material-symbols-outlined').click(function(){
        var currentState = $(this).text();
        $(this).parent().next().slideToggle(400);
        $(this).parent().find('span').text(currentState == expandSign ? collapseSign : expandSign );
    })
})