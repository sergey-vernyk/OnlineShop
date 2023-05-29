from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Coupon(models.Model):
    """
    Модель купона для покупки
    """

    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField(null=False)
    valid_to = models.DateTimeField(null=False)
    discount = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    category = models.ForeignKey('Category', related_name='coupons', on_delete=models.CASCADE, default='')

    def __str__(self):
        return f'Coupon "{self.code}"'

    @property
    def is_valid(self) -> bool:
        """
        Возврат состояния купона
        """
        now = timezone.now()
        return self.valid_from <= now <= self.valid_to


class Category(models.Model):
    """
    Модель категории купона
    """
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
