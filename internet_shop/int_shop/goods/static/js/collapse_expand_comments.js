$(document).ready(function() {
    $('.show-comments, .hide-comments').click(function() {
        var collapsedComments = $('.collapse-comm'); //all blocks, that have to be hidden

        if(collapsedComments && $(collapsedComments).is(':hidden')) {
            $(collapsedComments).slideDown(500);
            $('.show-comments').hide();
            $('.hide-comments').css({'display': 'inline-block'}).show();
        } else {
            $(collapsedComments).slideUp(500);
            $('.show-comments').show();
            $('.hide-comments').hide();
        }
    })
})