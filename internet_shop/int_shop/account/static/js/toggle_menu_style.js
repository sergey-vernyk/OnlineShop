$(document).ready(function() {

    //block with base information
    var parentSidebarCustomer = $('.sidebar-customer').parent();

    toggleMenuStyle(1000); //toggle to another menu style while loading

    $(window).on('resize', function() {
        toggleMenuStyle(1000);
    })
    
    function toggleMenuStyle(minWidth) {
        
        /* function changes menu style from vertical to horizontal
        depending on screen width minWidth */

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