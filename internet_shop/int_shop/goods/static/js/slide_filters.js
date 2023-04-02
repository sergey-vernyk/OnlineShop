$(document).ready(function() {
    // если меню свернуто - отобразить и наоборот
    if ($(".col-sm-2").css("visibility") == "collapse"){
        $(".col-sm-2").show();
    } else{
        $(".col-sm-2").hide();
    }
    // появление и исчезновение меню
    $("#filters-prod").click(function() {
        $(".col-sm-2").fadeToggle(500);
    });
//    $(".nav > li > a").not("#filters-prod").click(function() {
//        $(".col-sm-2").fadeOut(700);
//    });
});