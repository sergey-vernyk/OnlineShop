$(document).ready(function() {
    const eyeSign = 'material-symbols-outlined';

    //обработка события нажатия на значок глаза на поле формы
    $(`.auth-form-fields .${eyeSign},
     .reg-form-fields .${eyeSign},
     .set-new-pass-fields .${eyeSign}`).click(function() {
        var currentInput = $(this).prev();  //определение input, который принадлежит нажатому значку глаза
        var currentVisibilityState = $(currentInput).prop('type') === 'password' ? 'off' : 'on';

        //скрьтие или отображение вводимого пароля и изменения значка
        if(currentVisibilityState === 'on') {
            $(currentInput).prop('type', 'password');
            $(this).text('visibility_off');
        } else if(currentVisibilityState === 'off') {
            $(currentInput).prop('type', 'text');
            $(this).text('visibility');
        }
    })
})