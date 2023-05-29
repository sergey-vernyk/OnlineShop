import getCookie from '/static/js/getCSRFToken.js';

$(document).ready(function() {
    //стили 'закрашенного и не закрашенного' пальца для like/unlike
    const cssFillThumb = {'font-variation-settings': `"FILL" 1, "GRAD" 0, "opsz" 48, "wght" 400`};
    const cssUnfillThumb = {'font-variation-settings': `"FILL" 0, "GRAD" 0, "opsz" 48, "wght" 400`};
    const url = $('.comment-like-unlike-block').data('url');
    const csrftoken = getCookie('csrftoken');
   
    $('[id^=like-], [id^=unlike-]').click(function() {
        var commentId = $(this).attr('id').split('-')[1];
        var clickAction = $(this).attr('id').startsWith('like') ? 'like': 'unlike';
        var previousStatus = $(this).css('font-variation-settings').includes(`"FILL" 1`) ? 'set' : 'unset';

        switch (clickAction) {
            case 'like':
                if(previousStatus == 'unset') {
                    $(this).css(cssFillThumb);
                    $(`#unlike-${commentId}`).css(cssUnfillThumb); //сброс противоположного действия
                } else if(previousStatus == 'set') {
                    $(this).css(cssUnfillThumb);
                }

                break;
            case 'unlike':
                if(previouseStatus == 'set') {
                    $(this).css(cssUnfillThumb);
                } else if(previousStatus == 'unset') {
                    $(this).css(cssFillThumb);
                    $(`#like-${commentId}`).css(cssUnfillThumb); //сброс противоположного действия
                }

                break;
            default:
                break;
        }
        
        $.ajax({
            url: url,
            method: 'POST',
            dataType: 'json',
            data: {
                csrfmiddlewaretoken: csrftoken,
                comment_id: commentId,
                action: clickAction,
            },
            success: function(response) {
                //установка новых значений кол-ва лайков/дизлайков
                $(`#likes-count-${commentId}`).text(`(${response['new_count_likes']})`);
                $(`#unlikes-count-${commentId}`).text(`(${response['new_count_unlikes']})`);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus, errorThrown);
            },
        })
    })

    $('.comment-like-unlike-block').tooltip({
        content: "Awesome title!",
        items: '[id^=like-], .comment-like-unlike-block',
        tooltipClass: "tip",
        position: { my: "right top", at: "left center", collision: "none"},
    });

    var items = $( '.comment-like-unlike-block' ).tooltip( "option", "items" );
    var position = $( '.comment-like-unlike-block' ).tooltip( "option", "position" );
    console.log(items);
    console.log(position);
   
})