$(document).ready(function() {
    //if menu is collapse or open products filter result page - will show menu
    if ($('.filter-prod-column').css("visibility") === "collapse" || location.href.includes('filter')) {
        $('.filter-prod-column').show();
    } else {
        $('.filter-prod-column').hide();
    }
    //appearance and disappearance of the menu
    $('#filters-prod').click(function() {
        $('.filter-prod-column').fadeToggle(500);
    });
});