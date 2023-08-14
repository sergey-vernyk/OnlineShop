$(document).ready(function() {
    $('#main-nav-item').click(function() {
        var dropdownElements = $('.dropdwn').children().not(this); //searching all dropdown items

        window.onclick = function(event) {
            var target = $(event.target);
            //hiding dropdown menu, if there was click on anywhere place of the display, except for a menu item
            if (!target.is('.dropdwn > li')) {
                dropdownElements.hide();
            } else {
                dropdownElements.show();
            }
        };

    })
})