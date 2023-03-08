from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth import password_validation


class LoginForm(AuthenticationForm):
    """
    Форма для входа пользователя на сайт
    """
    username = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control w-25 mb-4'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control w-25 mb-4'}))
    remember = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'form-check-input mb-4'}),
                                  label='Remember me', required=False)


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

    user_photo = forms.ImageField(label='Photo', widget=forms.FileInput(attrs={'class': 'form-control w-25'}))

    field_order = ('username', 'first_name', 'last_name',
                   'email', 'date_of_birth', 'password1',
                   'password2', 'user_photo')
