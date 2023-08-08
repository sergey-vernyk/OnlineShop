from django.test import TestCase, RequestFactory, Client
from django.utils import timezone
from datetime import datetime
from django.shortcuts import reverse
from django.contrib.auth.models import User
from account.models import Profile
from django.conf import settings
import json

from orders.forms import OrderCreateForm, DeliveryCreateForm


class TestOrderCreateForm(TestCase):

    def setUp(self):
        settings.CELERY_TASK_ALWAYS_EAGER = True
        self.factory = RequestFactory()
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='password')
        self.profile = Profile.objects.create(user=self.user)

        self.data_order_form = {
            'order_form-first_name': 'Sergey',
            'order_form-last_name': 'Vernigora',
            'order_form-email': 'example@mail.com',
            'order_form-address': 'Address',
            'order_form-phone': '+38 (099) 123 45 67',
            'order_form-pay_method': 'Online',
            'order_form-comment': 'Some comment',
            'order_form-call_confirm': True,

            'delivery_form-first_name': 'Sergey',
            'delivery_form-last_name': 'Vernyk',
            'delivery_form-service': 'New Post',
            'delivery_form-method': 'Self-delivery',
            'delivery_form-office_number': '1',
            'delivery_form-delivery_date': datetime.strftime(
                datetime.now().date() + timezone.timedelta(days=3), '%d-%m-%Y'
            )
        }

    def test_invalid_phone_number(self):
        """
        Проверка отображение ошибки формы при неправильно введенном номере телефона
        """

        self.data_order_form.update({'order_form-phone': '+38 (099) 123 45 678'})  # в номере телефона больше цифр
        self.instance = OrderCreateForm(self.data_order_form)

        self.client.login(username=self.user.username, password=self.user.password)
        self.factory.post(reverse('orders:order_create'), data=self.data_order_form)
        # проверка валидности данных в форме и наличие ошибки поля с телефоном
        self.instance.is_valid()
        self.assertTrue(self.instance.has_error('phone'))
        # получение текста ошибки с json данных и ее соответствие
        error_data = self.instance.errors.as_json()
        data_json = json.loads(error_data)
        self.assertEqual(data_json['phone'][0]['message'], 'Invalid phone number')

    def test_invalid_delivery_date(self):
        """
        Проверка отображение ошибки поля даты доставки, когда была передана дата в прошлом времени
        """
        self.data_order_form.update({'delivery_form-delivery_date': datetime.strftime(
            datetime.now().date() + timezone.timedelta(days=-3), '%d-%m-%Y')})  # дата доставки в прошлом

        self.instance = DeliveryCreateForm(self.data_order_form)
        self.client.login(username=self.user.username, password=self.user.password)
        self.factory.post(reverse('orders:order_create'), data=self.data_order_form)
        self.assertTrue(self.instance.has_error('delivery_date', code='past_date'))