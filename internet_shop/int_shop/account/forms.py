from typing import Union

from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
    PasswordResetForm,
    SetPasswordForm
)
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from common.moduls_init import redis
from .models import Profile

help_messages = (
    'Your password must contain at least 8 characters and can’t be entirely numeric.',
    'Enter the same password as before, for verification.'
)


class LoginForm(AuthenticationForm):
    """
    Form for login user
    """
    username = forms.CharField(max_length=50, label='Username or Email',
                               widget=forms.TextInput(attrs={'class': 'auth-field'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'auth-field'}))
    remember = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'check-auth-field'}),
                                  label='Remember?', required=False)

    def clean_username(self) -> Union[str, ValidationError]:
        """
        Checking whether user is existing using received username or email
        """
        username_or_email = self.cleaned_data.get('username')

        if '@' in username_or_email:  # if was received email as username
            try:
                validate_email(username_or_email)
            except ValidationError as ve:
                raise ve
            else:
                try:
                    user = User.objects.get(email=username_or_email)
                    # user is not active
                    if not user.is_active:
                        raise ValidationError('User with this email doesn\'t active', code='inactive_user')
                    return user.username
                except ObjectDoesNotExist:
                    raise ValidationError('User with this email doesn\'t exists', code='No_exists_user')
        else:  # if was got not email as username
            user = User.objects.filter(username=username_or_email).exists()
            if not user:
                raise ValidationError('User with this username doesn\'t exist', code='No_exists_user')
            # user in not active
            elif not User.objects.get(username=username_or_email).is_active:
                raise ValidationError('User with this username doesn\'t active', code='inactive_user')

            return username_or_email

    def clean_password(self):
        """
        Exception if received password not match with received username
        """
        password = self.cleaned_data.get('password')
        username = self.cleaned_data.get('username')

        user_exists = User.objects.filter(username=username).exists()
        if user_exists:
            user = User.objects.get(username=username)
            # conformity checking received password and username
            password_correct = user.check_password(password)

            if not password_correct:
                raise ValidationError('Username with the input password are mismatch', code='wrong_password')

        return password


class UserPasswordChangeForm(PasswordChangeForm):
    """
    Form for changing password of user account
    """
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'pass-field',
                                                                     'autocomplete': 'new-password'}),
                                   help_text='If you have forgotten old password, click "Forgot password?" below.')
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'pass-field', 'autocomplete': 'new-password'}),
        label='New Password', help_text=help_messages[0]
    )
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'pass-field'}),
                                    label='New password confirmation',
                                    help_text=help_messages[1])


class RegisterUserForm(UserCreationForm):
    """
    Form for creating site's profile
    """
    username = forms.CharField(required=True, label='Username', widget=forms.TextInput(attrs={'class': 'reg-field'}))
    email = forms.CharField(required=True, label='Email', widget=forms.EmailInput(attrs={'class': 'reg-field'}))
    phone_number = forms.CharField(required=False, label='Phone',
                                   widget=forms.TextInput(attrs={'class': 'reg-field',
                                                                 'placeholder': '+x (xxx) xxx xx xx'}))
    password1 = forms.CharField(required=True, label='Password', widget=forms.PasswordInput(
        attrs={'class': 'reg-field', 'autocomplete': 'new-password'}),
                                help_text=help_messages[0])
    password2 = forms.CharField(required=True, label='Confirm password', widget=forms.PasswordInput(
        attrs={'class': 'reg-field', 'autocomplete': 'new-password'}),
                                help_text=help_messages[1])

    first_name = forms.CharField(required=True, label='First name',
                                 widget=forms.TextInput(attrs={'class': 'reg-field'}))
    last_name = forms.CharField(required=False, label='Last name', widget=forms.TextInput(attrs={'class': 'reg-field'}))
    date_of_birth = forms.DateField(required=False, label='Date of birth', widget=forms.DateInput(
        attrs={'class': 'reg-field', 'placeholder': 'dd-mm-yyyy'}))
    about = forms.CharField(label='About', required=False, widget=forms.Textarea(attrs={'rows': 6, 'cols': 5,
                                                                                        'class': 'reg-field'}))

    gender = forms.CharField(required=False, label='Gender', widget=forms.RadioSelect(choices=Profile.GENDER))

    user_photo = forms.ImageField(required=False, label='Photo', widget=forms.FileInput(attrs={'class': 'reg-photo'}))

    captcha = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'reg-field-captcha'}))

    field_order = ('username', 'first_name', 'last_name', 'gender',
                   'email', 'phone_number', 'date_of_birth', 'password1',
                   'password2', 'user_photo', 'about', 'captcha')

    error_messages = {
        'date_of_birth': {
            'invalid': 'Incorrect date',
        }
    }

    def clean_username(self):
        """
        Checking whether user is existing in the system, otherwise rise an exception
        """
        username = self.cleaned_data.get('username')
        user = User.objects.filter(username=username).exists()
        if user:
            raise ValidationError('Username is already exist', code='exists_username')

        return username

    def clean_email(self):
        """
        Checking whether user is existing in the system
        with received email, otherwise rise an exception
        """
        email = self.cleaned_data.get('email')
        user = User.objects.filter(email=email).exists()
        if user:
            raise ValidationError('Email is already register', code='exists_email')

        return email

    def clean_captcha(self):
        """
        Checking whether user entered correct text from captcha, otherwise raise an exception
        """
        captcha = self.cleaned_data.get('captcha').upper()  # convert all symbols to upper case as well
        email = self.cleaned_data.get('email')

        # captcha text may be empty if user forgot enter his/her email while registration
        if email:
            correct_captcha = redis.hget(f'user_register_captcha:{email}', 'captcha_text').decode('utf-8').upper()
        else:
            raise ValidationError('Captcha is not correct', code='wrong_captcha')

        if captcha != correct_captcha:
            raise ValidationError('Captcha is not correct', code='wrong_captcha')

        return captcha


class ForgotPasswordForm(PasswordResetForm):
    """
    Form for entering email, which using for restore an account's forgot password
    """

    email = forms.EmailField(label='Email',
                             max_length=254,
                             widget=forms.EmailInput(attrs={'class': 'email-field',
                                                            'autocomplete': 'email'}))

    def clean_email(self) -> str:
        """
        Checking whether user is active in the system or
        whether existing email in the system
        with received email, otherwise rise an exception
        """
        email = self.cleaned_data.get('email')
        user = self.get_users(email)  # getting generator with user
        try:
            received_email = next(user).email  # getting user's email
        except StopIteration:
            raise ValidationError('Current email doesn\'t registered or user not active', code='No_exists_user')

        return received_email


class SetNewPasswordForm(SetPasswordForm):
    """
    Form for entering new password after reset the last
    """

    new_password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password',
                                          'class': 'pass-field'}),
        help_text=help_messages[0]
    )
    new_password2 = forms.CharField(
        label='Confirm new password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password',
                                          'class': 'pass-field'}),
        help_text=help_messages[1])

    error_messages = {
        "password_mismatch": 'The two password fields didn’t match.',
    }
