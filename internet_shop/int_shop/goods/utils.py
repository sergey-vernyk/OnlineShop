from goods.filters import get_max_min_price
from decimal import Decimal
from goods.forms import FilterByPriceForm, FilterByManufacturerForm
from goods.property_filters import get_property_for_mobile_phones, get_property_for_laptops


class GoodsContextMixin:
    def add_to_context(self, context, kwargs) -> dict:
        """
        Метод добавляет данные с kwargs в context
        """
        context['filter_price'] = FilterByPriceForm()
        context['filter_manufacturers'] = FilterByManufacturerForm()

        if kwargs['category_slug'] == 'mobile-phones':
            context['filter_props_mobile'] = get_property_for_mobile_phones()
        elif kwargs['category_slug'] == 'laptops':
            context['filter_props_laptop'] = get_property_for_laptops()

        if 'filter_price' in kwargs:
            min_price = Decimal(kwargs.get('filter_price')[0])
            max_price = Decimal(kwargs.get('filter_price')[1])
        else:
            max_price, min_price = get_max_min_price(category_slug=kwargs['category_slug'])

        context['filter_price'].fields['price_min'].initial = min_price
        context['filter_price'].fields['price_max'].initial = max_price

        return context
