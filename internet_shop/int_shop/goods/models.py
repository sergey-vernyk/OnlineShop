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
    properties = models.OneToOneField(to='Property', related_name='product_properties', on_delete=models.SET_NULL,
                                      null=True, blank=True)
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
    name = models.CharField(max_length=50, unique=True)
    slug = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Manufacturer'
        verbose_name_plural = 'Manufacturers'


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


class Property(models.Model):
    """
    Модель свойства для товара
    """
    TYPES_RAM = (
        ('DDR3', 'DDR3'),
        ('DDR4', 'DDR4'),
        ('DDR5', 'DDR5'),
    )

    TYPES_ROM = (
        ('HDD', 'Hard Disk Drive'),
        ('SSD', 'Solid State Drive'),
        ('SSD/HDD', 'Solid State Drive/Hard Disk Drive'),
        ('UFS', 'UFS'),
    )

    TYPES_GRAPHICS = (
        ('Discrete', 'D'),
        ('Integrated', 'I'),
        ('Integrated/Discrete', 'I/D'),
    )

    TYPES_USB = (
        ('USB v.2', '2'),
        ('USB v.3', '3'),
        ('USB v.2/USB v.3', '2/3'),
    )

    TYPES_MOBILE_CONNECT = (
        ('2G', '2G'),
        ('3G', '3G'),
        ('4G', '4G'),
        ('5G', '5G'),
    )

    TYPES_WIFI = (
        ('802.11 a/b/g/', '802.11 a/b/g/'),
        ('802.11 a/b/g/n', '802.11 a/b/g/n'),
        ('802.11 a/b/g/n/ac', '802.11 a/b/g/n/ac'),
    )

    TYPES_OS = (
        ('Linux', 'Linux'),
        ('MacOS', 'MacOS'),
        ('Windows', 'Windows'),
        ('Android', 'Android'),
        ('IOS', 'IOS'),
    )

    TYPES_SCREEN = (
        ('OLED', 'OLED'),
        ('TFT', 'TFT'),
        ('IPS', 'IPS'),
    )
    # Дисплей
    screen_diagonal = models.CharField(max_length=5, verbose_name='Screen Diagonal', blank=True)
    screen_resolution = models.CharField(max_length=15, verbose_name='Screen Resolution', blank=True)
    screen_type = models.CharField(choices=TYPES_SCREEN, max_length=4, verbose_name='Scree Type', blank=True)
    # Процессор
    cpu = models.CharField(max_length=30, verbose_name='CPU model', blank=True)
    cpu_freq = models.CharField(max_length=50, verbose_name='CPU Frequency', blank=True)
    cpu_cores = models.CharField(max_length=10, verbose_name=' # CPU Cores', blank=True)
    # ОЗУ
    ram_type = models.CharField(choices=TYPES_RAM, max_length=4, verbose_name='RAM Type', blank=True)
    ram_value = models.CharField(max_length=10, verbose_name='RAM Capacity', blank=True)
    # Постоянная память
    rom_value = models.CharField(max_length=10, verbose_name='ROM Capacity', blank=True)
    rom_type = models.CharField(choices=TYPES_ROM, max_length=7, verbose_name='ROM Type', blank=True)
    # Графика
    graphics_type = models.CharField(choices=TYPES_GRAPHICS, max_length=20, verbose_name='Graphic Type', blank=True)
    graphics_ram_value = models.CharField(max_length=40, verbose_name='RAM Graphic', blank=True)
    # ОС
    operation_system = models.CharField(choices=TYPES_OS, max_length=8, verbose_name='Operation System', blank=True)
    # Интерфейсы
    hdmi = models.BooleanField(verbose_name='HDMI', blank=True)
    wifi_type = models.CharField(choices=TYPES_WIFI, max_length=20, verbose_name='WI-FI', blank=True)
    usb_type = models.CharField(choices=TYPES_USB, max_length=15, verbose_name='USB', blank=True)
    bluetooth = models.CharField(max_length=20, verbose_name='Bluetooth', blank=True)
    # Связь
    connection = models.CharField(choices=TYPES_MOBILE_CONNECT, max_length=2, verbose_name='Connections', blank=True)
    # Автономная работа
    work_time = models.DecimalField(verbose_name='Working time, Hours', max_digits=6, decimal_places=2, blank=True)
    # Корпус
    dimensions = models.CharField(max_length=50, verbose_name='Dimensions', blank=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Weight', blank=True)
    material = models.CharField(max_length=50, verbose_name='Material', blank=True)
    # Комплетация
    equipment = models.CharField(max_length=255, blank=True, verbose_name='Equipment')
    # Камера
    camera_main = models.CharField(max_length=50, verbose_name='Main Camera', blank=True)
    camera_front = models.CharField(max_length=50, verbose_name='Front Camera', blank=True)
    # Батарея
    battery_cap = models.CharField(max_length=30, verbose_name='Battery Capacity', blank=True)
    quick_charge = models.BooleanField(verbose_name='Quick Charge', blank=True)
    charge_power = models.IntegerField(verbose_name='Power Charge', blank=True)
    # Датчики
    sensors = models.CharField(max_length=200, verbose_name='Sensors', blank=True)

    class Meta:
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'

    def __str__(self):
        return f'Product Property id:{self.pk}'

    def __iter__(self):
        for prop, value in zip(self._meta.fields, list(self.__dict__.values())[1:]):
            if prop.verbose_name != 'ID':
                yield prop.verbose_name, value
