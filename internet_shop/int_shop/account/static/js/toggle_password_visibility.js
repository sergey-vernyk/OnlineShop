$(document).ready(function() {
    const eyeSign = 'material-symbols-outlined';

    //handling "eye" icon pressing event on form field
    $(`.auth-form-fields .${eyeSign},
     .reg-form-fields .${eyeSign},
     .set-new-pass-fields .${eyeSign}`).click(function() {
        var currentInput = $(this).prev();  //recognize input, on which were pressed on "eye" icon
        var currentVisibilityState = $(currentInput).prop('type') === 'password' ? 'off' : 'on';

        //hide or show typing password and changing icon
        if(currentVisibilityState === 'on') {
            $(currentInput).prop('type', 'password');
            $(this).text('visibility_off');
        } else if(currentVisibilityState === 'off') {
            $(currentInput).prop('type', 'text');
            $(this).text('visibility');
        }
    })
})