$(document).ready(function() {
    // если меню свернуто или открыта станица с результатами фильтров - отобразить меню
    if ($('.filter-prod-column').css("visibility") === "collapse" || location.href.includes('filter')) {
        $('.filter-prod-column').show();
    } else {
        $('.filter-prod-column').hide();
    }
    // появление и исчезновение меню
    $('#filters-prod').click(function() {
        $('.filter-prod-column').fadeToggle(500);
    });
});