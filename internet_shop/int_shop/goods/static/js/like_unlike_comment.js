import getCookie from '/static/js/getCSRFToken.js';

$(document).ready(function() {
    //styles for "filled" and no "unfilled" thumbs for like/dislike стили
    const cssFillThumb = {'font-variation-settings': `"FILL" 1, "GRAD" 0, "opsz" 48, "wght" 400`};
    const cssUnfillThumb = {'font-variation-settings': `"FILL" 0, "GRAD" 0, "opsz" 48, "wght" 400`};
    const url = $('.comment-like-unlike-block').data('url');
    const csrftoken = getCookie('csrftoken');
   
    $('[id^=like-], [id^=unlike-]').click(function() {
        const currentButton = $(this);
        var commentId = $(this).attr('id').split('-')[1];
        var clickAction = $(this).attr('id').startsWith('like') ? 'like': 'unlike';
        var previousStatus = $(this).css('font-variation-settings').includes(`"FILL" 1`) ? 'set' : 'unset';
        
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
                switch (clickAction) {
                    case 'like':
                        if(previousStatus == 'unset') {
                            $(currentButton).css(cssFillThumb);
                            $(`#unlike-${commentId}`).css(cssUnfillThumb); //reset opposite action
                        } else if(previousStatus == 'set')
                            $(currentButton).css(cssUnfillThumb);

                        break;
                    case 'unlike':
                        if(previousStatus == 'set') {
                            $(currentButton).css(cssUnfillThumb);
                        } else if(previousStatus == 'unset') {
                            $(currentButton).css(cssFillThumb);
                            $(`#like-${commentId}`).css(cssUnfillThumb); //reset opposite action
                        }
        
                        break;
                    default:
                        break;
                }
                //setting new values of quantity likes/dislikes
                $(`#likes-count-${commentId}`).text(`(${response['new_count_likes']})`);
                $(`#unlikes-count-${commentId}`).text(`(${response['new_count_unlikes']})`);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                //if user is not authenticated - show up window with an information
                if(errorThrown === 'Unauthorized') {
                    var login_url = jqXHR.responseJSON['login_page_url']
                    // translate windows's strings for other languges
                    const formats = django.gettext(
                        '<div id="dialog">Please <a href="%s">login</a> to be able to rate comments!</div>', login_url
                    )
                    const content = django.interpolate(formats, [login_url])

                    var commentRatePanel = $(`#comment-pk-${commentId}`).children().first();

                    $(content).dialog({
                        height: 75,
                        width: 250,
                        resizable: false,
                        draggable: false,
                        title: django.gettext('Unauthorized'),
                        show: { effect: "fadeIn", duration: 500 },
                        hide: { effect: "fadeOut", duration: 500 },
                        classes: {
                            'ui-dialog-titlebar': 'dialog-rate-comment-titlebar',
                            'ui-dialog-title': 'dialog-rate-comment-title',
                            'ui-dialog-content': 'dialog-rate-comment-content',
                        },
                        position: {my: "right center", at: "right-24% center", of: commentRatePanel}
                      });
                }
            },
        })
    })
})