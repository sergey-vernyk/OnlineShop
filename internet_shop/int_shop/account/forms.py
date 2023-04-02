from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth import password_validation
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .models import Profile


class LoginForm(AuthenticationForm):
    """
    Форма для входа пользователя на сайт
    """
    username = forms.CharField(required=False, max_length=50, label='Username/Email',
                               widget=forms.TextInput(attrs={'class': 'form-control mb-2',
                                                             'placeholder': 'Username/Email'}))
    password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control mb-2',
                                                                                 'placeholder': 'Password'}))
    remember = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'form-check-input mb-2'}),
                                  label='Remember?', required=False)

    def clean_username(self):
        """
        Проверка существующего пользователя
        по введенному username или email
        """
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username')

        # если не было передано username или email
        if not username_or_email:
            raise ValidationError('Please enter a correct username')
        if '@' in username_or_email:
            try:
                validate_email(username_or_email)
            except ValidationError as ve:
                return ve
            else:
                try:
                    user = User.objects.get(email=username_or_email)
                    return user.username
                except ObjectDoesNotExist as oe:
                    pass
        else:
            return username_or_email

    def clean_password(self):
        """
        Исключение, если не был передан пароль
        """
        cleaned_data = super().clean()
        if not cleaned_data.get('password'):
            raise ValidationError('Please enter a correct password')


class UserPasswordChangeForm(PasswordChangeForm):
    """
    Форма для изменения пароля учетной записи пользователя
    """
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control w-25',
                                                                     'autocomplete': 'new-password'}),
                                   help_text=password_validation.password_validators_help_text_html())
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control w-25',
                                                                      'autocomplete': 'new-password'}),
                                    label='New Password')
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control w-25'}),
                                    label='New password confirmation')


class RegisterUserForm(UserCreationForm):
    """
    Форма для создания пользователя сайта
    """
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'class': 'form-control w-25'}))
    email = forms.CharField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control w-25'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(
        attrs={'class': 'form-control w-25', 'autocomplete': 'new-password'}),
                                help_text=password_validation.password_validators_help_text_html())
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput(
        attrs={'class': 'form-control w-25', 'autocomplete': 'new-password'}),
                                help_text="Enter the same password as before, for verification.")

    first_name = forms.CharField(label='First name', widget=forms.TextInput(attrs={'class': 'form-control w-25'}))
    last_name = forms.CharField(label='Last name', widget=forms.TextInput(attrs={'class': 'form-control w-25'}))
    date_of_birth = forms.DateField(label='Date of birth', widget=forms.DateInput(attrs={'class': 'form-control w-25'}),
                                    help_text='Format: yyyy-mm-dd')

    gender = forms.CharField(required=False, label='Gender', widget=forms.RadioSelect(choices=Profile.GENDER))

    user_photo = forms.ImageField(required=False, label='Photo',
                                  widget=forms.FileInput(attrs={'class': 'form-control w-25'}))

    field_order = ('username', 'first_name', 'last_name', 'gender',
                   'email', 'date_of_birth', 'password1',
                   'password2', 'user_photo')
