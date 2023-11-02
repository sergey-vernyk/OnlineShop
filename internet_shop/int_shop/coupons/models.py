from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatedFields, TranslatableModel


class Coupon(models.Model):
    """
    Coupon model for purchases.
    """

    code = models.CharField(max_length=50, unique=True, verbose_name=_('Code'))
    valid_from = models.DateTimeField(null=False, verbose_name=_('Valid from'))
    valid_to = models.DateTimeField(null=False, verbose_name=_('Valid to'))
    discount = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)],
                                           verbose_name=_('Discount'))
    category = models.ForeignKey('Category',
                                 related_name='coupons',
                                 on_delete=models.CASCADE,
                                 default='',
                                 verbose_name=_('Category'))

    def __str__(self):
        return f'Coupon "{self.code}"'

    @property
    def is_valid(self) -> bool:
        """
        Returns coupon state.
        """
        now = timezone.now()
        return self.valid_from <= now <= self.valid_to

    class Meta:
        ordering = ('id',)
        verbose_name = _('Coupon')
        verbose_name_plural = _('Coupons')


class Category(TranslatableModel):
    """
    Coupon category model.
    """
    translations = TranslatedFields(
        name=models.CharField(max_length=50, verbose_name=_('Name')),
        slug=models.SlugField(max_length=50, verbose_name=_('Slug')),
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ('id',)
