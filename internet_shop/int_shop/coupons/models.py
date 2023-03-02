from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Coupon(models.Model):
    """
    Модель купона для покупки
    """

    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField(null=False)
    valid_to = models.DateTimeField(null=False)
    discount = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    active = models.BooleanField(default=False)
    category = models.ForeignKey('Category', related_name='coupons', on_delete=models.CASCADE, default='')

    def __str__(self):
        return f'Coupon "{self.code}"'


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
