from .models import Property, PropertyCategory


# TODO refactoring
def get_property_for_mobile_phones() -> list:
    """
    Функция получает необходимые для поиска свойства
    мобильных телефонов
    """

    # необходимые свойства товара для фильтра
    needed_props = (
        {'Display': ('Diagonal', 'Resolution', 'Type'),
         'CPU': ('Cores',),
         'Camera': ('Front', 'Main'),
         'Communications': ('SIM', 'NFC'),
         'Battery': ('Capacity',),
         'Internal Memory': ('Volume',),
         'Software': ('OS',),
         'RAM Memory': ('Volume',)}
    )

    # получаем категории свойств, характерных для мобильных телефонов
    # получаем id этих категорий
    # получаем значения свойств в виде списка словарей с определенными значениями

    properties_categories = PropertyCategory.objects.filter(
        product_categories__name__iexact='Mobile phones').values_list()
    properties_categories_ids = tuple(map(lambda x: x[0], properties_categories))
    properties = Property.objects.filter(
        category_property__id__in=properties_categories_ids,
        product__category__name__iexact='Mobile Phones').distinct().values('name',
                                                                           'text_value',
                                                                           'numeric_value',
                                                                           'units',
                                                                           'category_property__name',
                                                                           'category_property__pk')
    # отбор нужных категорий и свойств для отображения поиска
    result = [p for p in properties if p['category_property__name'] in needed_props
              and p['name'] in needed_props[p['category_property__name']]]

    # сортировка результатов по имени категории свойств, затем имени свойства
    return sorted(result, key=lambda x: (x['category_property__name'], x['name']))


def get_property_for_laptops() -> list:
    """
    Функция получает необходимые для поиска свойства
    ноутбуков
    """

    # необходимые свойства товара для фильтра
    needed_props = (
        {'Display': ('Diagonal', 'Resolution', 'Type'),
         'CPU': ('Cores', 'Model'),
         'Camera': ('Resolution',),
         'Communications': ('Bluetooth', 'HDMI', 'LAN'),
         'Battery': ('Work time',),
         'Internal Memory': ('Volume', 'Type'),
         'Software': ('OS',),
         'RAM Memory': ('Volume',),
         'Body': ('Color', 'Material'),
         'Video': ('Form Factor', 'Model', 'Volume')}
    )

    # получаем категории свойств, характерных для ноутбуков
    # получаем id этих категорий
    # получаем значения свойств в виде списка словарей с определенными значениями

    properties_categories = PropertyCategory.objects.filter(
        product_categories__name__iexact='Laptops').values_list()
    properties_categories_ids = tuple(map(lambda x: x[0], properties_categories))
    properties = Property.objects.filter(
        category_property__id__in=properties_categories_ids,
        product__category__name__iexact='Laptops').distinct().values('name',
                                                                     'text_value',
                                                                     'numeric_value',
                                                                     'units',
                                                                     'category_property__name',
                                                                     'category_property__pk')
    # отбор нужных категорий и свойств для отображения поиска
    result = [p for p in properties if p['category_property__name'] in needed_props
              and p['name'] in needed_props[p['category_property__name']]]

    # сортировка результатов по имени категории свойств, затем имени свойства
    return sorted(result, key=lambda x: (x['category_property__name'], x['name']))
