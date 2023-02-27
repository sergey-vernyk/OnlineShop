from django.shortcuts import render
from django.contrib.auth.views import LoginView

from account.forms import LoginForm


class LoginUserView(LoginView):
    form_class = LoginForm
