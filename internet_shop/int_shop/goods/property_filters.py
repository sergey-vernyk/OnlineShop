from typing import Union

from django.core.cache import cache
from django.db.models import F, Q
from django.db.models import QuerySet
from django.db.models.aggregates import Count
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _, gettext

from .models import Property, PropertyCategory

MOBILE_PHONES_NECESSARY_PROPS = {
    gettext('Display'): (_('Diagonal'), _('Resolution'), _('Type')),
    gettext('CPU'): (_('Cores'),),
    gettext('Camera'): (_('Front'), _('Main')),
    gettext('Communications'): ('SIM', 'NFC'),
    gettext('Battery'): (_('Capacity'),),
    gettext('Internal Memory'): (_('Volume'),),
    gettext('Software'): (_('OS'),),
    gettext('RAM Memory'): (_('Volume'),)
}

LAPTOPS_NECESSARY_PROPS = {
    'Display': (_('Diagonal'), _('Resolution'), _('Type')),
    'CPU': (_('Cores'), _('Model')),
    'Camera': (_('Resolution'),),
    'Communications': ('Bluetooth', 'HDMI', 'LAN'),
    'Battery': (_('Work time'),),
    'Internal Memory': (_('Volume'), _('Type')),
    'Software': (_('OS'),),
    'RAM Memory': (_('Volume'),),
    gettext('Body'): (_('Color'), _('Material')),
    gettext('Video'): (_('Form Factor'), _('Model'), _('Volume'))
}

AUDIO_VIDEO_NECESSARY_PROPS = {
    'Communications': ('Bluetooth', 'WI-FI'),
    'Battery': (_('Work Time'), _('Charging'),),
    gettext('Audio'): (_('Channels'), _('Power'), _('Inputs')),
    'Video': (_('Resolution'),),
    gettext('Photo'): (_('Resolution'), _('Image sensor')),
    'Body': (_('Form Factor'),)
}

SMART_GADGETS_NECESSARY_PROPS = {
    'Display': (_('Diagonal'), _('Resolution'), _('Type')),
    'Camera': (_('Resolution'),),
    'Communications': ('Bluetooth', 'WI-FI'),
    'Battery': (_('Work time'), _('Charging Port')),
    'Internal Memory': (_('Volume'),),
    'Body': (_('Color'), _('Material'))
}


def get_property_for_category(products_category: str,
                              language_code: str,
                              prods_queryset: Union[QuerySet, None] = None) -> dict:
    """
    Returns necessary properties for passed `products_category`.
    """
    necessary_props = None
    rest_props = None
    lookup = Q()

    properties = {
        'Mobile phones': MOBILE_PHONES_NECESSARY_PROPS,
        'Laptops': LAPTOPS_NECESSARY_PROPS,
        'Audio Video': AUDIO_VIDEO_NECESSARY_PROPS,
        'Smart Gadgets': SMART_GADGETS_NECESSARY_PROPS
    }

    necessary_props = properties.get(products_category, {})

    if prods_queryset:
        lookup = Q(product__in=prods_queryset)

    # getting queryset from cache
    all_props = cache.get(
        f'category_{slugify(products_category)}_props_{language_code}')
    if not all_props:
        properties_categories = PropertyCategory.objects.prefetch_related('product_categories').filter(
            translations__language_code=language_code)

        lookup &= Q(category_property__in=properties_categories,
                    product__category__name__iexact=products_category,
                    product__available=True)
        all_props = Property.objects.prefetch_related('category_property', 'translations').filter(
            lookup, translations__language_code=language_code)
        # saving queryset to cache
        cache.set(
            f'category_{slugify(products_category)}_props_{language_code}', all_props)

    if prods_queryset:
        # remaining filtered products properties
        rest_props = all_props.filter(lookup, translations__language_code=language_code)

    # select necessary categories and properties for searching
    result = {}
    for prop in (rest_props or all_props).select_related('category_property').values('translations__name',
                                                                                     'translations__text_value',
                                                                                     'numeric_value',
                                                                                     'translations__units',).annotate(
            category_property=F('category_property__translations__name'),
            category_property_pk=F('category_property_id'),
            item_count=Count('translations__name')).order_by('category_property'):
        if (prop['category_property'] in necessary_props and
                prop['translations__name'] in necessary_props[prop['category_property']]):
            result.setdefault(gettext(prop['category_property']), []).append(prop)

    return result
