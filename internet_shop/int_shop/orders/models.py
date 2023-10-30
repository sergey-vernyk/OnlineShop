from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from account.models import Profile
from coupons.models import Coupon
from goods.models import Product
from present_cards.models import PresentCard


class Order(models.Model):
    """
    Order model.
    """
    METHOD_PAY = (
        ('Online', _('Online')),
        ('On delivery', _('On delivery')),
        ('Installments', _('Installments')),
    )

    first_name = models.CharField(max_length=30, verbose_name=_('First name'))
    last_name = models.CharField(max_length=30, verbose_name=_('Last name'))
    email = models.EmailField(verbose_name=_('Email'))
    address = models.CharField(max_length=255, blank=True, verbose_name=_('Address'))
    phone = models.CharField(max_length=20, verbose_name=_('Phone'))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created'))
    updated = models.DateTimeField(auto_now=True, verbose_name=_('Updated'))
    comment = models.TextField(max_length=100, blank=True, verbose_name=_('Comment'))
    call_confirm = models.BooleanField(default=False, verbose_name=_('Call confirm'))
    pay_method = models.CharField(choices=METHOD_PAY, max_length=20, verbose_name=_('Pay method'))
    is_paid = models.BooleanField(default=False, verbose_name=_('Paid'))
    is_done = models.BooleanField(default=False, verbose_name=_('Done'))
    present_card = models.OneToOneField(PresentCard,
                                        related_name='order',
                                        on_delete=models.SET_NULL,
                                        null=True,
                                        blank=True,
                                        verbose_name=_('Present card'))
    coupon = models.ForeignKey(Coupon,
                               related_name='orders',
                               on_delete=models.SET_NULL,
                               null=True,
                               blank=True,
                               verbose_name=_('Coupon'))
    delivery = models.OneToOneField('Delivery',
                                    related_name='order',
                                    on_delete=models.SET_NULL,
                                    null=True,
                                    verbose_name=_('Delivery'))
    stripe_id = models.CharField(max_length=255, blank=True, verbose_name=_('Stripe id'))
    profile = models.ForeignKey(Profile,
                                related_name='orders',
                                on_delete=models.CASCADE,
                                default='',
                                verbose_name=_('User profile'))

    def __str__(self):
        return f'id: {self.pk} - {self.first_name} {self.last_name}'

    def get_total_values(self) -> dict:
        """
        Method returns dictionary with amount values such as:
        total cost without discounts, total cost with discounts, and total discount amount
        """
        totals = {
            'total_cost': sum(item.get_cost() for item in self.items.all()),
            'total_cost_with_discounts': Decimal('0.00'),
            'total_discounts': Decimal('0.00')
        }

        coupon, present_card = self.coupon, self.present_card

        if coupon:
            totals['total_cost_with_discounts'] = totals['total_cost'] - (totals['total_cost'] * coupon.discount / 100)
        elif present_card:
            totals['total_cost_with_discounts'] = totals['total_cost'] - present_card.amount

        if any([coupon, present_card]):
            totals['total_discounts'] = totals['total_cost'] - totals['total_cost_with_discounts']

        return {k: v.quantize(Decimal('0.01')) for k, v in totals.items()}  # rounds result to 2 signs

    class Meta:
        ordering = ('-created',)
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')


class Delivery(models.Model):
    """
    Delivery model.
    """

    DELIVERY_METHOD = (
        ('Self-delivery', _('Self-delivery')),
        ('Post office', _('Post office')),
        ('Apartment', _('Apartment')),
    )

    DELIVERY_SERVICES = (
        ('New Post', _('New Post')),
        ('Ukrpost', _('Ukrpost')),
        ('Meest Express', _('Meest Express')),
    )

    first_name = models.CharField(max_length=30, verbose_name=_('First name'))
    last_name = models.CharField(max_length=30, verbose_name=_('Last name'))
    service = models.CharField(choices=DELIVERY_SERVICES, max_length=15, blank=True, verbose_name=_('Service'))
    method = models.CharField(choices=DELIVERY_METHOD, max_length=20, verbose_name=_('Method'))
    office_number = models.IntegerField(blank=True, validators=[MinValueValidator(0)], null=True,
                                        verbose_name=_('Office number'))
    delivery_date = models.DateField(verbose_name=_('Delivery date'))

    def __str__(self):
        return f'Delivery method "{self.method}"'

    class Meta:
        ordering = ('delivery_date',)
        verbose_name = _('Delivery')
        verbose_name_plural = _('Deliveries')


class OrderItem(models.Model):
    """
    Order items model.
    """
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name=_('Order'))
    product = models.ForeignKey(Product,
                                related_name='order_items',
                                on_delete=models.CASCADE,
                                verbose_name=_('Product'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Price'))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_('Quantity'))

    class Meta:
        ordering = ('order_id',)
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')

    def __str__(self):
        return f'Order item "{self.pk}"'

    def get_cost(self):
        """
        Calculate amount cost of the order items taking in account their quantity.
        """
        return self.price * self.quantity
