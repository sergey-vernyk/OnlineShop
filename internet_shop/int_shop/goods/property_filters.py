from django.core.cache import cache
from django.db.models import F, Q
from django.db.models.aggregates import Count
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .models import Property, PropertyCategory

mobile_phones_necessary_props = (
    {'Display': ('Diagonal', 'Resolution', 'Type'),
     'CPU': ('Cores',),
     'Camera': ('Front', 'Main'),
     'Communications': ('SIM', 'NFC'),
     'Battery': ('Capacity',),
     'Internal Memory': ('Volume',),
     'Software': ('OS',),
     'RAM Memory': ('Volume',)}
)

laptops_necessary_props = (
    {'Display': (_('Diagonal'), _('Resolution'), _('Type')),
     'CPU': (_('Cores'), _('Model')),
     'Camera': (_('Resolution'),),
     'Communications': ('Bluetooth', 'HDMI', 'LAN'),
     'Battery': (_('Work time'),),
     'Internal Memory': (_('Volume'), _('Type')),
     'Software': ('OS',),
     'RAM Memory': (_('Volume'),),
     'Body': (_('Color'), _('Material')),
     'Video': (_('Form Factor'), _('Model'), _('Volume'))}
)

audio_video_necessary_props = (
    {'Communications': ('Bluetooth', 'WI-FI'),
     'Battery': ('Work Time', 'Charging',),
     'Audio': ('Channels', 'Power', 'Inputs'),
     'Video': ('Resolution',),
     'Photo': ('Resolution', 'Image sensor'),
     'Body': ('Form Factor',)}
)

smart_gadgets_necessary_props = (
    {'Display': ('Diagonal', 'Resolution', 'Type'),
     'Camera': ('Resolution',),
     'Communications': ('Bluetooth', 'WI-FI'),
     'Battery': ('Work time', 'Charging Port'),
     'Internal Memory': ('Volume',),
     'Body': ('Color', 'Material')}
)


def get_property_for_category(products_category: str, language_code: str, prods_queryset=None) -> dict:
    """
    Returns necessary properties for each `products_category`.
    """
    necessary_props = None
    rest_props = None
    lookup = Q()

    if products_category == 'Mobile phones':
        necessary_props = mobile_phones_necessary_props
    elif products_category == 'Laptops':
        necessary_props = laptops_necessary_props
    elif products_category == 'Audio Video':
        necessary_props = audio_video_necessary_props
    elif products_category == 'Smart Gadgets':
        necessary_props = smart_gadgets_necessary_props

    if prods_queryset:
        lookup = Q(product__in=prods_queryset)

    all_props = cache.get(f'category_{slugify(products_category)}_props_{language_code}')  # getting queryset from cache
    if not all_props:
        properties_categories = PropertyCategory.objects.prefetch_related('product_categories')
        lookup &= Q(category_property__in=properties_categories,
                    product__category__name__iexact=products_category,
                    product__available=True)
        all_props = Property.objects.select_related('category_property').filter(
            lookup, translations__language_code=language_code)
        cache.set(f'category_{slugify(products_category)}_props_{language_code}', all_props)  # saving queryset to cache

    if prods_queryset:
        rest_props = all_props.filter(lookup)  # remaining filtered products properties

    # select necessary categories and properties for searching
    result = {}
    for prop in (rest_props or all_props).select_related('category_property').values('translations__name',
                                                                                     'text_value',
                                                                                     'numeric_value',
                                                                                     'units').annotate(
        category_property=F('category_property__name'),
        category_property_pk=F('category_property_id'),
        item_count=Count('translations__name')).order_by('category_property'):
        if (prop['category_property'] in necessary_props and
                prop['translations__name'] in necessary_props[prop['category_property']]):
            result.setdefault(prop['category_property'], []).append(prop)

    return result
