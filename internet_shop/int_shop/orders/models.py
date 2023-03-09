from django.db import models

from coupons.models import Coupon
from goods.models import Product
from present_cards.models import PresentCard


class Order(models.Model):
    """
    Модель заказа
    """
    METHOD_PAY = (
        ('Online', 'Online'),
        ('On delivery', 'On delivery'),
        ('Installments', 'Installments'),
    )

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    address = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    recipient = models.CharField(max_length=100, blank=True)
    comment = models.TextField(max_length=100, blank=True)
    call_confirm = models.BooleanField(default=False)
    pay_method = models.CharField(choices=METHOD_PAY, max_length=20)
    is_paid = models.BooleanField(default=False)
    present_card = models.OneToOneField(PresentCard, related_name='order', on_delete=models.SET_NULL,
                                        null=True, blank=True)
    coupon = models.ForeignKey(Coupon, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True)
    delivery = models.OneToOneField('Delivery', related_name='order', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'Order {self.first_name} {self.last_name}'

    class Meta:
        ordering = ('-created',)


class Delivery(models.Model):
    """
    Модель доставки товара
    """

    DELIVERY_METHOD = (
        ('Self-delivery', 'Self-delivery'),
        ('Post office', 'Post office'),
        ('Apartment', 'Apartment'),
    )

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    method = models.CharField(choices=DELIVERY_METHOD, max_length=20)
    office_number = models.IntegerField(blank=True, null=True)
    delivery_date = models.DateField()

    def __str__(self):
        return f'Delivery method "{self.method}"'

    class Meta:
        ordering = ('delivery_date',)
        verbose_name = 'Delivery'
        verbose_name_plural = 'Deliveries'


class OrderItem(models.Model):
    """
    Модель единиц в заказе
    """
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'Order item "{self.pk}"'
