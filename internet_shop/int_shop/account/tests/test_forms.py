from django.test import TestCase, Client, RequestFactory
from django.shortcuts import reverse
from account.forms import LoginForm, RegisterUserForm, ForgotPasswordForm
from django.contrib.auth.models import User

from account.models import Profile
from goods.models import Favorite


class TestAccountForms(TestCase):
    """
    Testing forms for the account application
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
        Checking successfully login while entering correct data (user exists in the system)
        """

        response = self.client.post(reverse('login'), {'username': self.user.username, 'password': 'password'})
        self.assertRedirects(response, reverse('goods:product_list'))  # redirecting to the main page
        self.assertTrue(self.user.is_authenticated)  # user is authenticated

        # email like username
        response = self.client.post(reverse('login'), {'username': self.user.email, 'password': 'password'})
        self.assertRedirects(response, reverse('goods:product_list'))
        self.assertTrue(self.user.is_authenticated)

    def test_enter_incorrect_data_to_login_form(self):
        """
        Checking if the user exists by it username or email
        """
        # user name doesn't exists
        request = self.factory.post(reverse('login'), {'username': 'no_exists_user', 'password': 'password'})
        instance = LoginForm(data=request.POST)
        self.assertTrue(instance.has_error('username', code='No_exists_user'))

        # email doesn't exists
        request = self.factory.post(reverse('login'), {'username': 'mail@mail.com', 'password': 'password'})
        instance = LoginForm(data=request.POST)
        self.assertTrue(instance.has_error('username', code='No_exists_user'))

        # invalid email
        request = self.factory.post(reverse('login'), {'username': 'mail@mail', 'password': 'password'})
        instance = LoginForm(data=request.POST)
        self.assertTrue(instance.has_error('username', code='invalid'))

        # wrong password
        request = self.factory.post(reverse('login'), {'username': self.user.username, 'password': 'wrong-password'})
        instance = LoginForm(data=request.POST)
        self.assertTrue(instance.has_error('password', code='wrong_password'))

        # user is inactive
        self.user.is_active = False
        self.user.save()

        for name in (self.user.username, self.user.email):
            request = self.factory.post(reverse('login'), {'username': name, 'password': 'password'})
            instance = LoginForm(data=request.POST)
            self.assertTrue(instance.has_error('username', code='inactive_user'))

    def test_enter_exists_username_during_registration(self):
        """
        Checking the raise an error while submitting registration,
        when entered username, that exists in the system
        """
        request = self.factory.post(reverse('register_user'), {'username': self.user.username})
        instance = RegisterUserForm(request.POST)
        self.assertTrue(instance.has_error('username', code='exists_username'))  # that username exists

    def test_enter_exists_email_during_registration(self):
        """
        Checking the raise an error while submitting registration,
        when entered email, that exists in the system
        """
        request = self.factory.post(reverse('register_user'), {'email': self.user.email})
        instance = RegisterUserForm(request.POST)
        self.assertTrue(instance.has_error('email', code='exists_email'))  # that email exists

    def test_enter_not_exists_email_relative_with_register_user(self):
        """
        Checking the raise an error, when transmitting not exists email
        while user attempt to recover forgotten account password
        """
        request = self.factory.post(reverse('password_reset'), {'email': 'no_exists@example.com'})
        instance = ForgotPasswordForm(request.POST)
        self.assertTrue(instance.has_error('email', code='No_exists_user'))
