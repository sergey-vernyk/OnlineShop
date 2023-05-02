$(document).ready(function(){
    $('[id^=comment-]').click(function() {
        var comment_id = $(this).attr('id').slice(8);
        $(`#comment-expander-${comment_id}`).slideToggle();
    })
})