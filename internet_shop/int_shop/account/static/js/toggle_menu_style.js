$(document).ready(function() {

    //блок с основной информацией    
    var parentSidebarCustomer = $('.sidebar-customer').parent();

    toggleMenuStyle(1000); //переключение на другое меню при загрузке страницы

    $(window).on('resize', function() {
        toggleMenuStyle(1000);
    })
    
    function toggleMenuStyle(minWidth) {
        
        /* функция изменяет вид меню с вертикального на горизонтальный,
        в зависимости от ширины экрана minWidth */

        if ($(window).width() <= minWidth) {
            $('.sidebar-customer').addClass('sidebar-customer-horizontal')
            $(parentSidebarCustomer).addClass('flex-column');
            $('.content-customer').removeClass('content-customer-width-v').addClass('content-customer-width-h') 
        } else {
            $('.sidebar-customer').removeClass('sidebar-customer-horizontal')
            $(parentSidebarCustomer).removeClass('flex-column');
            $('.content-customer').removeClass('content-customer-width-h').addClass('content-customer-width-v'); 
        }
    }
})  