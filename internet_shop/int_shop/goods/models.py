from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.urls import reverse
from decimal import Decimal

from account.models import Profile


class Product(models.Model):
    """
    Модель товара на сайте
    """

    class Rating(models.IntegerChoices):
        ZERO_STARS = 0, '0'
        ONE_STAR = 1, '1'
        TWO_STARS = 2, '2'
        THREE_STARS = 3, '3'
        FOUR_STARS = 4, '4'
        FIVE_STARS = 5, '5'

    star = models.IntegerField(choices=Rating.choices, default=Rating.ZERO_STARS, verbose_name='Rating')

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    manufacturer = models.ForeignKey('Manufacturer', on_delete=models.SET_NULL, related_name='products', null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')
    rating = models.DecimalField(default=0, max_digits=2, decimal_places=1, validators=[MinValueValidator(Decimal(0.0)),
                                                                                        MaxValueValidator(
                                                                                            Decimal(5.0))])

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('goods:product_detail', args=(self.pk, self.slug))

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ('name',)


class Favorite(models.Model):
    """
    Модель товаров, добавленных в избранное определенным пользователем
    """
    product = models.ManyToManyField(Product, blank=True)
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='profile_favorite')
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f'Profile "{self.profile.user.username}"'


class Category(models.Model):
    """
    Модель категории товаров на сайте
    """
    name = models.CharField(max_length=50, db_index=True)
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('goods:product_list_by_category', args=(self.slug,))

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class Manufacturer(models.Model):
    """
    Класс производителя товара
    """
    name = models.CharField(max_length=50)
    slug = models.CharField(max_length=50, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Manufacturer'
        verbose_name_plural = 'Manufacturers'
        ordering = ('name',)


class Comment(models.Model):
    """
    Модель комментария для товара на сайте
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    user_name = models.CharField(max_length=30, verbose_name='Name')
    user_email = models.EmailField(default='', verbose_name='Email')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='profile_comments', default='')
    body = models.TextField(verbose_name='Review Text')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'"{self.body[:20]}..."'

    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'


class PropertyCategory(models.Model):
    """
    Модель категории свойств,
    например, свойства для дисплея, памяти, аккумулятора и т.д.
    """

    name = models.CharField(max_length=100)
    product_categories = models.ManyToManyField(Category)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Property Category'
        verbose_name_plural = 'Property Categories'


class Property(models.Model):
    """
    Модель отдельного свойства для товара
    """

    name = models.CharField(max_length=50)
    value = models.CharField(max_length=255)
    units = models.CharField(max_length=10, blank=True)
    detail_description = models.TextField(max_length=255, blank=True)
    category_property = models.ForeignKey(PropertyCategory,
                                          related_name='category_properties',
                                          on_delete=models.CASCADE,
                                          default='')
    product = models.ForeignKey(Product, related_name='properties', on_delete=models.CASCADE, default='')

    class Meta:
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'
        ordering = ('category_property',)

    def __str__(self):
        return f'{self.category_property}: {self.name}'
