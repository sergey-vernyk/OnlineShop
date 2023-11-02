from decimal import Decimal
from django_filters import rest_framework as filters
from django.db.models import Q


class ProductFilter(filters.FilterSet):
    """
    Filter allows to obtain products either by their properties, or
    within min and max price, or product's manufacturer
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._property_name = None

    @property
    def pr_name(self):
        return self._property_name.title()

    @pr_name.setter
    def pr_name(self, value):
        if isinstance(value, str):
            self._property_name = value

    price_min = filters.NumberFilter(field_name='price', lookup_expr='gte', label='Minimum product price')
    price_max = filters.NumberFilter(field_name='price', lookup_expr='lte', label='Maximum product price')
    manufacturer = filters.CharFilter(field_name='manufacturer', lookup_expr='name__iexact', label='Manufacturer')
    prop_name = filters.CharFilter(method='properties_filter_name', label='Property name')
    category_prop_name = filters.CharFilter(field_name='properties',
                                            label='Category property name',
                                            lookup_expr='category_property__name__iexact',
                                            distinct=True)
    prop_value_lte = filters.NumberFilter(method='properties_filter_value', label='Numeric property value <=')
    prop_value_gte = filters.NumberFilter(method='properties_filter_value', label='Numeric property value >=')
    prop_value_text = filters.CharFilter(field_name='properties__text_value',
                                         lookup_expr='iexact',
                                         label='Text property value')

    def properties_filter_value(self, queryset, name, value):
        """
        Returns queryset with products, which have specific property name `property_name` ,
        and the property name numeric value within `lte` and `gte`
        """
        lookup = Q()
        if name.endswith('lte'):
            lookup &= Q(properties__numeric_value__lte=Decimal(value))
        else:
            lookup &= Q(properties__numeric_value__gte=Decimal(value))

        return queryset.filter(
            lookup & Q(properties__name=self.pr_name)
        )

    def properties_filter_name(self, queryset, name, value):
        self.pr_name = value
        return queryset.filter(properties__name__iexact=value)
