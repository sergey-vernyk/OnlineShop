from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm, PasswordResetForm, \
    SetPasswordForm
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .models import Profile
from datetime import datetime

help_messages = ('Your password must contain at least 8 characters and can’t be entirely numeric.',
                 'Enter the same password as before, for verification.')


class LoginForm(AuthenticationForm):
    """
    Форма для входа пользователя на сайт
    """
    username = forms.CharField(max_length=50, label='Username or Email',
                               widget=forms.TextInput(attrs={'class': 'auth-field'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'auth-field'}))
    remember = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'check-auth-field'}),
                                  label='Remember?', required=False)

    error_messages = {
        'invalid_login':
            'Please enter a correct %(username)s or password',
        'inactive': 'This account is inactive',
    }

    def clean_username(self):
        """
        Проверка существующего пользователя
        по введенному username или email
        """
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username')

        # если не было передано username или email
        if not username_or_email:
            raise ValidationError('Please, enter a correct username')

        if '@' in username_or_email:  # если был передан адрес электронной почты
            try:
                validate_email(username_or_email)
            except ValidationError as ve:
                raise ve
            else:
                try:
                    user = User.objects.get(email=username_or_email)
                    return user.username
                except ObjectDoesNotExist:
                    raise ValidationError('User with this email doesn\'t exist')
        else:  # если было передано имя пользователя
            user = User.objects.filter(username=username_or_email).exists()
            if not user:
                raise ValidationError('User with this username doesn\'t exist')

            return username_or_email

    def clean_password(self):
        """
        Исключение, если не был передан пароль
        """
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        if not password:
            raise ValidationError('Please, enter a correct password')

        return password


class UserPasswordChangeForm(PasswordChangeForm):
    """
    Форма для изменения пароля учетной записи пользователя
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
    Форма для создания пользователя сайта
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

    user_photo = forms.ImageField(required=False, label='Photo',
                                  widget=forms.FileInput(attrs={'class': 'reg-photo'}))

    field_order = ('username', 'first_name', 'last_name', 'gender',
                   'email', 'phone_number', 'date_of_birth', 'password1',
                   'password2', 'user_photo', 'about')

    error_messages = {
        'date_of_birth': {
            'invalid': 'Incorrect date',
        }
    }

    def clean_username(self):
        """
        Проверка существования пользователя
        в системе и исключение, если такой пользователь уже есть
        """
        username = self.cleaned_data.get('username')
        user = User.objects.filter(username=username).exists()
        if user:
            raise ValidationError('Username is already exist')

        return username

    def clean_email(self):
        """
        Проверка существования пользователя с email адресом
        в системе и исключение, если такой адрес уже есть
        """
        email = self.cleaned_data.get('email')
        user = User.objects.filter(email=email).exists()
        if user:
            raise ValidationError('Email is already register')

        return email


class ForgotPasswordForm(PasswordResetForm):
    """
    Форма для ввода email адреса для восстановления забытого пароля
    от учетной записи
    """

    email = forms.EmailField(label='Email',
                             max_length=254,
                             widget=forms.EmailInput(attrs={'class': 'email-field',
                                                            'autocomplete': 'email'}))

    def clean_email(self) -> str:
        """
        Проверка существования активного пользователя
        или существующего адреса в системе с введенным в форму email
        """
        email = self.cleaned_data.get('email')
        user = self.get_users(email)  # получения генератора с пользователем
        try:
            received_email = next(user).email  # получение email пользователя
        except StopIteration:
            raise ValidationError('Current email doesn\'t registered or user not active')

        return received_email


class SetNewPasswordForm(SetPasswordForm):
    """
    Форма для ввода нового пароля после сброса
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
