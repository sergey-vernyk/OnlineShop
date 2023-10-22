import os
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields

from account.models import Profile
from common.moduls_init import redis


class AvailableProductsManager(models.Manager):
    """
    Custom manager, which returns products, which marked as available
    """

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(available=True)


def get_product_image_path(instance, filename):
    """
    Returns the save image path for each product
    """
    return f'products/product_{instance.name}/{filename}'


class Product(models.Model):
    """
    Product model
    """

    class Rating(models.IntegerChoices):
        ONE_STAR = (1, '1')
        TWO_STARS = (2, '2')
        THREE_STARS = (3, '3')
        FOUR_STARS = (4, '4')
        FIVE_STARS = (5, '5')

    star = models.IntegerField(choices=Rating.choices, default=Rating.ONE_STAR, verbose_name='Rating')

    name = models.CharField(max_length=100, verbose_name=_('Name'))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_('Slug'))
    manufacturer = models.ForeignKey('Manufacturer',
                                     on_delete=models.SET_NULL,
                                     related_name='products',
                                     null=True,
                                     verbose_name=_('Manufacturer'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Price'))
    description = models.TextField(verbose_name=_('Description'))
    image = models.ImageField(upload_to=get_product_image_path, blank=True, verbose_name=_('Image'))
    available = models.BooleanField(default=True, verbose_name=_('Available'))
    promotional = models.BooleanField(default=False, verbose_name=_('Promotional'))
    promotional_price = models.DecimalField(max_digits=10,
                                            decimal_places=2,
                                            default=Decimal('0.00'),
                                            verbose_name=_('Promotional price'))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created date'))
    updated = models.DateTimeField(auto_now=True, verbose_name=_('Updated date'))
    category = models.ForeignKey('Category',
                                 on_delete=models.CASCADE,
                                 related_name='products',
                                 verbose_name=_('Category'))
    rating = models.DecimalField(default=0.0,
                                 max_digits=2,
                                 decimal_places=1,
                                 validators=[MinValueValidator(Decimal(0.0)), MaxValueValidator(Decimal(5.0))],
                                 verbose_name=_('Rating'))

    available_objects = AvailableProductsManager()
    objects = models.Manager()

    def __str__(self):
        return self.name

    def get_all_product_photos(self) -> list:
        """
        Returns names of all product images in list format
        """
        return os.listdir(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.name}', 'Detail_photos'))

    def save(self, *args, **kwargs):
        """
        Overriding the method to add the id of created product the set in Redis DB,
        and creating directories for storage product's picture
        """
        super().save(*args, **kwargs)
        try:
            os.makedirs(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.name}', 'Detail_photos'))
        except FileExistsError:
            pass
        redis.sadd('products_ids', self.pk)

    def get_absolute_url(self):
        """
        Returns canonical path to the product in detail view
        """
        return reverse('goods:product_detail', args=(self.pk, self.slug))

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ('name',)


class Favorite(models.Model):
    """
    Profile's favorite products model
    """
    product = models.ManyToManyField(Product, blank=True, verbose_name=_('Product'))
    profile = models.OneToOneField(Profile,
                                   on_delete=models.CASCADE,
                                   related_name='profile_favorite',
                                   verbose_name=_('Profile'))
    created = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_('Created date'))

    def __str__(self):
        return f'Profile "{self.profile.user.username}"'

    class Meta:
        verbose_name = _('Favorite')
        verbose_name_plural = _('Favorites')


class Category(models.Model):
    """
    Products category model
    """
    name = models.CharField(max_length=50, db_index=True, verbose_name=_('Name'))
    slug = models.SlugField(max_length=50, unique=True, verbose_name=_('Slug'))

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """
        Returns canonical path to the product in certain category in detail view
        """
        return reverse('goods:product_list_by_category', args=(self.slug,))

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ('name',)


class Manufacturer(models.Model):
    """
    Products manufacturer model
    """
    name = models.CharField(max_length=50, verbose_name=_('Name'))
    slug = models.CharField(max_length=50, unique=True, verbose_name=_('Slug'))
    description = models.TextField(verbose_name=_('Description'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Manufacturer')
        verbose_name_plural = _('Manufacturers')
        ordering = ('name',)


class Comment(models.Model):
    """
    Product comment model
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='comments',
                                verbose_name=_('Product'))
    user_name = models.CharField(max_length=30, verbose_name=_('Name'))
    user_email = models.EmailField(default='', verbose_name=_('Email'))
    profile = models.ForeignKey(Profile,
                                on_delete=models.CASCADE,
                                related_name='profile_comments',
                                default='',
                                verbose_name=_('Profile'))
    body = models.TextField(verbose_name=_('Comment'))
    profiles_likes = models.ManyToManyField(Profile,
                                            related_name='comments_liked',
                                            blank=True,
                                            default=0,
                                            verbose_name=_('Profile\'s likes'))
    profiles_unlikes = models.ManyToManyField(Profile,
                                              related_name='comments_unliked',
                                              blank=True,
                                              default=0,
                                              verbose_name=_('Profile\'s dislikes'))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created date'))
    updated = models.DateTimeField(auto_now=True, verbose_name=_('Updated date'))

    def __str__(self):
        return f'"{self.body[:20]}..."'

    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')


class PropertyCategory(models.Model):
    """
    Property category model.
    For example for display, memory, battery ect.
    """

    name = models.CharField(max_length=100, verbose_name=_('Name'))
    product_categories = models.ManyToManyField(Category, verbose_name=_('Products Categories'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Property Category')
        verbose_name_plural = _('Property Categories')


class Property(TranslatableModel):
    """
    Product property.
    """
    property_names = (sorted([
        # Display
        (_('Colors'), _('Colors')), (_('Diagonal'), _('Diagonal')), (_('Pixel Density'), _('Pixel Density')),
        (_('Type'), _('Type')), (_('Resolution'), _('Resolution')), (_('Brightness'), _('Brightness')),
        (_('Sweep frequency'), _('Sweep frequency')),
        # CPU
        (_('#Cores'), _('#Cores')), (_('Frequency'), _('Frequency')), (_('Model'), _('Model')),
        (_('Threads'), _('Threads')),
        # Camera
        (_('Front'), _('Front')),
        (_('Main'), _('Main')),
        # Communication
        ('Bluetooth', 'Bluetooth'), ('NFC', 'NFC'), (_('Positioning'), _('Positioning')), (_('Radio'), _('Radio')),
        ('SIM', 'SIM'), (_('Speed'), _('Speed')), ('USB', 'USB'), ('WI-FI', 'WI-FI'),
        (_('Audio Port'), _('Audio Port')), ('HDMI', 'HDMI'), ('LAN', 'LAN'), ('4G', '4G'), ('5G', '5G'),
        # Battery
        (_('Capacity'), _('Capacity')), (_('Charging'), _('Charging')), (_('Quick Charge'), _('Quick Charge')),
        (_('#Cells'), _('#Cells')), (_('Work Time'), _('Work Time')), (_('Charging Port'), _('Charging Port')),
        # Body
        (_('Color'), _('Color')), (_('Dimensions'), _('Dimensions')), (_('Material'), _('Material')),
        (_('Weight'), _('Weight')), (_('Opening Angle'), _('Opening Angle')),
        # Audio
        (_('Manufacturer'), _('Manufacturer')), (_('Power'), _('Power')), (_('Frequency Range'), _('Frequency Range')),
        (_('Interfaces'), _('Interfaces')), (_('Inputs'), _('Inputs')), (_('Supply Types'), _('Supply Types')),
        (_('Connections'), _('Connections')), (_('Channels'), _('Channels')),
        # RAM Memory
        (_('Volume'), _('Volume')),
        (_('#Slots'), _('#Slots')),
        # Security
        (_('Firmware'), _('Firmware')),
        # Video
        (_('Form Factor'), _('Form Factor')),
        # Photo
        ('FOV', 'FOV'), (_('Image sensor'), _('Image sensor')),
        # Internal Memory
        (_('Card slot'), _('Card slot')),
        # Features
        (_('Sensors'), _('Sensors')),
        (_('Keyboard Lightening'), _('Keyboard Lightening')),
        (_('Additional Features'), _('Additional Features')),
        # Software
        (_('OS'), _('OS')),
        (_('User interface'), _('User interface')),
        (_('Version'), _('Version')),
        # Other
        (_('Packaging'), _('Packaging'))

    ], key=lambda x: x[0]))

    translations = TranslatedFields(
        name=models.CharField(max_length=50, choices=property_names, default='', verbose_name=_('Property name'))
    )

    text_value = models.CharField(max_length=255, blank=True, verbose_name=_('Text value'))
    numeric_value = models.DecimalField(max_digits=6, decimal_places=2, blank=True, default='0.00',
                                        verbose_name=_('Numeric value'))
    units = models.CharField(max_length=10, blank=True, verbose_name=_('Units'))
    detail_description = models.TextField(max_length=600, blank=True, verbose_name=_('Detail description'))
    category_property = models.ForeignKey(PropertyCategory,
                                          related_name='category_properties',
                                          on_delete=models.CASCADE,
                                          default='',
                                          verbose_name=_('Category property'))
    product = models.ForeignKey(Product,
                                related_name='properties',
                                on_delete=models.CASCADE,
                                default='',
                                verbose_name=_('Product'))

    class Meta:
        verbose_name = _('Property')
        verbose_name_plural = _('Properties')
        ordering = ('category_property',)

    def __str__(self):
        return f'{self.category_property}: {self.name}'
