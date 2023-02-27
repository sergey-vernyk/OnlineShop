from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    """
    Форма для входа пользователя на сайт
    """
    username = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control w-25'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control w-25'}))
