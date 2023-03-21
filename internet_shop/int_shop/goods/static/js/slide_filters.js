$(document).ready(function() {
    // если меню свернуто - отобразить и наоборот
    if ($(".col-sm-2").css("visibility") == "collapse"){
        $(".col-sm-2").show();
    } else{
        $(".col-sm-2").hide();
    }
    // появление и исчезновение меню
    $("#filters-prod").click(function() {
        $(".col-sm-2").slideDown(800);
    });
    $(".nav > li > a").not("#filters-prod").click(function() {
        $(".col-sm-2").slideUp(700);
    });
});