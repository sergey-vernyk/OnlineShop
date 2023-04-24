from django.db import models
from decimal import Decimal
from account.models import Profile
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
    comment = models.TextField(max_length=100, blank=True)
    call_confirm = models.BooleanField(default=False)
    pay_method = models.CharField(choices=METHOD_PAY, max_length=20)
    is_paid = models.BooleanField(default=False)
    is_done = models.BooleanField(default=False)
    present_card = models.OneToOneField(PresentCard, related_name='order', on_delete=models.SET_NULL,
                                        null=True, blank=True)
    coupon = models.ForeignKey(Coupon, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True)
    delivery = models.OneToOneField('Delivery', related_name='order', on_delete=models.SET_NULL, null=True)
    stripe_id = models.CharField(max_length=255, blank=True)
    is_email_was_sent = models.BooleanField(default=False)
    profile = models.ForeignKey(Profile, related_name='orders', on_delete=models.CASCADE, default='')

    def __str__(self):
        return f'id: {self.pk} - {self.first_name} {self.last_name}'

    def get_total_cost(self) -> Decimal:
        """
        Общая сумма товаров в заказе
        """
        return sum(item.get_cost() for item in self.items.all())

    def get_total_discount(self) -> Decimal:
        """
        Общая сумма скидки
        """
        total_cost = self.get_total_cost()

        total_discount = Decimal('0')
        if self.coupon:
            total_discount += (total_cost * (self.coupon.discount / Decimal(100))).quantize(Decimal('0.01'))
        if self.present_card:
            total_discount += self.present_card.amount

        return total_discount

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

    def get_cost(self):
        """
        Подсчет суммарной стоимости единицы заказа,
        с учетом его количества
        """
        return self.price * self.quantity
