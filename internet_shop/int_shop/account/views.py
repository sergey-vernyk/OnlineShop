from django.shortcuts import render
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.views.generic import CreateView
from account.forms import LoginForm, UserPasswordChangeForm, RegisterUserForm
from django.urls import reverse_lazy

from account.models import Profile


class LoginUserView(LoginView):
    """
    Представление входа пользователя
    """
    form_class = LoginForm


class UserPasswordChangeView(PasswordChangeView):
    """
    Представление для изменения пароля
    пользовательского аккаунта
    """
    form_class = UserPasswordChangeForm


class UserRegisterView(CreateView):
    """
    Представление для регистрации пользователя в системе
    """
    form_class = RegisterUserForm
    template_name = 'registration/user_register_form.html'
    success_url = reverse_lazy('login')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            new_user = form.save(commit=False)  # создаем пользователя, но в базе не сохраняем
            date_of_birth = form.cleaned_data.get('date_of_birth')
            user_photo = form.cleaned_data.get('user_photo')
            # заполняем поля пользователя с данных формы
            new_user.username = form.cleaned_data.get('username')
            new_user.email = form.cleaned_data.get('email')
            new_user.first_name = form.cleaned_data.get('first_name')
            new_user.last_name = form.cleaned_data.get('last_name')
            new_user.save()  # сохраняем пользователя в базе
            # Создаем профиль пользователя с доп. полями
            Profile.objects.create(user=new_user,
                                   date_of_birth=date_of_birth,
                                   photo=user_photo)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
