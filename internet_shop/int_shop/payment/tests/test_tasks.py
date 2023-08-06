from django.test import TestCase
from django.conf import settings
from account.models import Profile
from django.contrib.auth.models import User
from decimal import Decimal
from payment.tasks import order_paid
from orders.models import Order


class TestPaymentTasks(TestCase):
    """
    Проверка celery задач
    """

    def setUp(self) -> None:
        settings.CELERY_TASK_ALWAYS_EAGER = True
        self.user = User.objects.create_user(username='user', password='password', email='example@example.com')
        self.profile = Profile.objects.create(user=self.user)

        self.order = Order.objects.create(first_name='Name',
                                          last_name='Surname',
                                          email='example@example.com',
                                          phone='+38 (099) 123 45 67',
                                          pay_method='Online',
                                          profile=self.profile)

    def test_order_paid(self):
        """
        Проверка отправки письма пользователю, который оплатил заказ
        """
        data = {
            'domain': 'testserver',
            'is_secure': False,
        }

        order_id = self.order.pk
        amount_total = Decimal('250.45')

        result = order_paid.delay(data, order_id, amount_total).get()
        self.assertEqual(result, 'Successfully')
