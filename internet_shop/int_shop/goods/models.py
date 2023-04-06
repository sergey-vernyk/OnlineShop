import redis
from django.conf import settings
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone

from account.models import Profile

r = redis.Redis(host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB)


def product_image_path(instance, filename):
    """
    Возвращает путь сохранения изображений для каждого товара
    """
    now = timezone.now()
    return f'products_{instance.name}/{now.strftime("%Y-%m-%d")}/{filename}'


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
    image = models.ImageField(upload_to=product_image_path, blank=True)
    available = models.BooleanField(default=True)
    promotional = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')
    rating = models.DecimalField(default=0, max_digits=2, decimal_places=1, validators=[MinValueValidator(Decimal(0.0)),
                                                                                        MaxValueValidator(
                                                                                            Decimal(5.0))])

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Переопределение метода, что бы добавить id созданного
        товара в список со всеми id товаров, которые хранятся в БД Redis
        """
        super().save(*args, **kwargs)
        r.lpush('products_ids', self.pk)

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
    property_names = (sorted([
        # Display
        ('Colors', 'Colors'), ('Diagonal', 'Diagonal'), ('Pixel Density', 'Pixel Density'), ('Type', 'Type'),
        ('Resolution', 'Resolution'), ('Brightness', 'Brightness'), ('Sweep frequency', 'Sweep frequency'),
        # CPU
        ('#Cores', '#Cores'), ('Frequency', 'Frequency'), ('Model', 'Model'), ('Threads', 'Threads'),
        # Camera
        ('Front', 'Front'),
        ('Main', 'Main'),
        # Communication
        ('Bluetooth', 'Bluetooth'), ('NFC', 'NFC'), ('Positioning', 'Positioning'), ('Radio', 'Radio'), ('SIM', 'SIM'),
        ('Speed', 'Speed'), ('USB', 'USB'), ('WI-FI', 'WI-FI'), ('Audio Port', 'Audio Port'), ('HDMI', 'HDMI'),
        ('LAN', 'LAN'), ('4G', '4G'), ('5G', '5G'),
        # Battery
        ('Capacity', 'Capacity'), ('Charging', 'Charging'), ('Quick Charge', 'Quick Charge'), ('#Cells', '#Cells'),
        ('Work Time', 'Work Time'),
        # Body
        ('Color', 'Color'), ('Dimensions', 'Dimensions'), ('Material', 'Material'), ('Weight', 'Weight'),
        ('Opening Angle', 'Opening Angle'),
        # Audio
        ('Manufacturer', 'Manufacturer'),
        ('Power', 'Power'),
        # RAM Memory
        ('Volume', 'Volume'),
        ('#Slots', '#Slots'),
        # Security
        ('Firmware', 'Firmware'),
        # Video
        ('Form Factor', 'Form Factor'),
        # Internal Memory
        ('Card slot', 'Card slot'),
        # Features
        ('Sensors', 'Sensors'),
        ('Keyboard Lightening', 'Keyboard Lightening'),
        # Software
        ('OS', 'OS'),
        ('User interface', 'User interface'),
        ('Version', 'Version'),

    ], key=lambda x: x[0]))

    name = models.CharField(max_length=50, choices=property_names)
    text_value = models.CharField(max_length=255, blank=True)
    numeric_value = models.DecimalField(max_digits=6, decimal_places=2, blank=True, default='0.00')
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
