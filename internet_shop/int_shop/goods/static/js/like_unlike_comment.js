import getCookie from '/static/js/getCSRFToken.js';

$(document).ready(function() {
    //стили 'закрашенного и не закрашенного' пальца для like/unlike
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
                            $(`#unlike-${commentId}`).css(cssUnfillThumb); //сброс противоположного действия
                        } else if(previousStatus == 'set') {
                            $(currentButton).css(cssUnfillThumb);
                        }
        
                        break;
                    case 'unlike':
                        if(previousStatus == 'set') {
                            $(currentButton).css(cssUnfillThumb);
                        } else if(previousStatus == 'unset') {
                            $(currentButton).css(cssFillThumb);
                            $(`#like-${commentId}`).css(cssUnfillThumb); //сброс противоположного действия
                        }
        
                        break;
                    default:
                        break;
                }
                //установка новых значений кол-ва лайков/дизлайков
                $(`#likes-count-${commentId}`).text(`(${response['new_count_likes']})`);
                $(`#unlikes-count-${commentId}`).text(`(${response['new_count_unlikes']})`);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                //если посльзователь не авторизован - вывести окно с информацией
                if(errorThrown === 'Unauthorized') {
                    var login_url = jqXHR.responseJSON['login_page_url']
                    const content = `<div id="dialog">Please <a href="${login_url}">login</a> to be able to rate comments!</div>`

                    var commentRatePanel = $(`#comment-pk-${commentId}`).children().first();

                    $(content).dialog({
                        height: 57,
                        width: 300,
                        resizable: false,
                        draggable: false,
                        title: 'Unauthorized',
                        show: { effect: "fadeIn", duration: 500 },
                        hide: { effect: "fadeOut", duration: 500 },
                        classes: {
                            'ui-dialog-titlebar': 'dialog-rate-comment-titlebar',
                            'ui-dialog-title': 'dialog-rate-comment-title',
                            'ui-dialog-content': 'dialog-rate-comment-content',
                        },
                        position: {my: "right center", at: "right-22% center", of: commentRatePanel}
                      });
                }
            },
        })
    })
})