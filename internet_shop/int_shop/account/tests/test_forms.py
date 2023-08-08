from django.test import TestCase, Client, RequestFactory
from django.shortcuts import reverse
from account.forms import LoginForm, RegisterUserForm, ForgotPasswordForm
from django.contrib.auth.models import User

from account.models import Profile
from goods.models import Favorite


class TestAccountForms(TestCase):
    """
    Тестирование форм приложения account
    """

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', password='password', email='example@example.com')
        self.profile = Profile.objects.create(user=self.user)
        Favorite.objects.create(profile=self.profile)
        self.user.set_password('password')
        self.client = Client()
        self.factory = RequestFactory()

    def test_successfully_login(self):
        """
        Проверка успешного входа в систему при вводе корректных данных (пользователь существует в системе)
        """

        response = self.client.post(reverse('login'), {'username': self.user.username, 'password': 'password'})
        self.assertRedirects(response, reverse('goods:product_list'))  # переадресация на главную страницу
        self.assertTrue(self.user.is_authenticated)  # пользователь теперь аутентифицирован

        # email в качестве username
        response = self.client.post(reverse('login'), {'username': self.user.email, 'password': 'password'})
        self.assertRedirects(response, reverse('goods:product_list'))
        self.assertTrue(self.user.is_authenticated)

    def test_enter_incorrect_data_to_login_form(self):
        """
        Проверка определения существования пользователя
        в системе по его username или его email
        """
        # не существующее имя пользователя
        request = self.factory.post(reverse('login'), {'username': 'no_exists_user', 'password': 'password'})
        instance = LoginForm(data=request.POST)
        self.assertTrue(instance.has_error('username', code='No_exists_user'))

        # не существующий email
        request = self.factory.post(reverse('login'), {'username': 'mail@mail.com', 'password': 'password'})
        instance = LoginForm(data=request.POST)
        self.assertTrue(instance.has_error('username', code='No_exists_user'))

        # не валидный email
        request = self.factory.post(reverse('login'), {'username': 'mail@mail', 'password': 'password'})
        instance = LoginForm(data=request.POST)
        self.assertTrue(instance.has_error('username', code='invalid'))

        # неправильный пароль
        request = self.factory.post(reverse('login'), {'username': self.user.username, 'password': 'wrong-password'})
        instance = LoginForm(data=request.POST)
        self.assertTrue(instance.has_error('password', code='wrong_password'))

        # пользователь не активен
        self.user.is_active = False
        self.user.save()

        for name in (self.user.username, self.user.email):
            request = self.factory.post(reverse('login'), {'username': name, 'password': 'password'})
            instance = LoginForm(data=request.POST)
            self.assertTrue(instance.has_error('username', code='inactive_user'))

    def test_enter_exists_username_during_registration(self):
        """
        Проверка возникновения ошибки при подтверждении регистрации,
        когда введен уже существующий в системе username
        """
        request = self.factory.post(reverse('register_user'), {'username': self.user.username})
        instance = RegisterUserForm(request.POST)
        self.assertTrue(instance.has_error('username', code='exists_username'))  # такой username уже есть в системе

    def test_enter_exists_email_during_registration(self):
        """
        Проверка возникновения ошибки при подтверждении регистрации,
        когда введен уже существующий в системе email
        """
        request = self.factory.post(reverse('register_user'), {'email': self.user.email})
        instance = RegisterUserForm(request.POST)
        self.assertTrue(instance.has_error('email', code='exists_email'))  # такой email уже есть в системе

    def test_enter_not_exists_email_relative_with_register_user(self):
        """
        Проверка возникновения ошибки, когда передается несуществующий
        в системе адрес электронной почты, при попытке восстановления забытого пароля от учетной записи
        """
        request = self.factory.post(reverse('password_reset'), {'email': 'no_exists@example.com'})
        instance = ForgotPasswordForm(request.POST)
        self.assertTrue(instance.has_error('email', code='No_exists_user'))
