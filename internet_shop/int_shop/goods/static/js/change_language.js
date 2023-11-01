$(document).ready(function() {

        const currentLang = $('[name=cur-lang]').val();
        //make language flag icons smaller, except current languge's icon flag
        $('.language-list').find('[id^=lang-]').not(`#lang-${currentLang}`).attr({'width': 25, 'height': 19})

        $('[id^=lang-]').on('click', function() {
            const form = $(this).parents('form');
            const selectedLang = $(this).attr('id').split('-')[1];
            // fill `value` attribute with current language code in hidden input
            $(form).find('[name=language]').attr('value', selectedLang);
            $(this).attr({'width': 26, 'height': 20});
            $(form).submit();
        })

})