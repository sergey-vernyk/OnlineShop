from django.test import TestCase
from orders.models import Order, Delivery
from account.models import Profile
from django.contrib.auth.models import User
from orders.admin import OrderAdmin, DeliveryAdmin
from django.contrib.admin.sites import AdminSite
from coupons.models import Coupon
from present_cards.models import PresentCard
from coupons.models import Category as Coupon_category
from present_cards.models import Category as Card_category
from django.utils import timezone


class TestOrdersAdmin(TestCase):
    """
    Проверка методов админ панели для заказов
    """

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='User', password='password')
        self.profile = Profile.objects.create(user=self.user)

        self.coupon = Coupon.objects.create(code='coupon_code',
                                            valid_from=timezone.now(),
                                            valid_to=timezone.now() + timezone.timedelta(days=10),
                                            discount=20,
                                            category=Coupon_category.objects.create(name='For men', slug='for-men'))

        self.card = PresentCard.objects.create(code='card_code',
                                               valid_from=timezone.now(),
                                               valid_to=timezone.now() + timezone.timedelta(days=10),
                                               amount=250.50,
                                               category=Card_category.objects.create(name='For men', slug='for-men'))

        self.site = AdminSite
        self.instance_order = OrderAdmin(model=Order, admin_site=self.site)
        self.instance_delivery = DeliveryAdmin(model=Delivery, admin_site=self.site)

    def test_get_discount_for_coupon(self):
        """
        Проверка правильности ссылки для перехода информации о купоне в заказе
        """
        order = Order.objects.create(first_name='Name',
                                     last_name='Surname',
                                     email='example@example.com',
                                     phone='+38 (099) 123 45 67',
                                     pay_method='Online',
                                     profile=self.profile,
                                     coupon=self.coupon)

        self.assertEqual(self.instance_order.get_discount(order),
                         '<a href="/admin/coupons/coupon/1/change/">Coupon</a>')

    def test_get_discount_for_present_card(self):
        """
        Проверка правильности ссылки для перехода информации о подарочной в заказе
        """
        order = Order.objects.create(first_name='Name',
                                     last_name='Surname',
                                     email='example@example.com',
                                     phone='+38 (099) 123 45 67',
                                     pay_method='Online',
                                     profile=self.profile,
                                     present_card=self.card)

        self.assertEqual(self.instance_order.get_discount(order),
                         '<a href="/admin/present_cards/presentcard/2/change/">Present Card</a>')

    def test_get_full_name_order_customer(self):
        """
        Проверка правильности отображения полного имени пользователя для заказа
        """
        order = Order.objects.create(first_name='Name',
                                     last_name='Surname',
                                     email='example@example.com',
                                     phone='+38 (099) 123 45 67',
                                     pay_method='Online',
                                     profile=self.profile,
                                     present_card=self.card)

        self.assertEqual(self.instance_order.get_full_name(order), 'Name Surname')

    def test_get_full_name_order_delivery(self):
        """
        Проверка правильности отображения полного имени пользователя для доставки
        """
        order = Delivery.objects.create(first_name='Name',
                                        last_name='Surname',
                                        service='New Post',
                                        method='Post office',
                                        office_number=1,
                                        delivery_date=timezone.now().date() + timezone.timedelta(days=3))

        self.assertEqual(self.instance_delivery.get_full_name(order), 'Name Surname')
