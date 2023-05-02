$(document).ready(function() {
    $('#main-nav-item').click(function() {
        var dropdownElements = $('.dropdwn').children().not(this); //поиск всех элементов выпадающего меню

        window.onclick = function(event) {
            var target = $(event.target);
            //скрытие выпадающего меню, если было нажатие на любом месте экрана, кроме элемента меню
            if (!target.is('.dropdwn > li')) {
                dropdownElements.hide();
            } else {
                dropdownElements.show();
            }
        };

    })
})