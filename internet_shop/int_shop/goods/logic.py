from typing import Union

from django.db.models import QuerySet
from decimal import Decimal
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page


def distribute_properties_from_request(properties: list) -> dict:
    """
    Функция собирает все принятые свойства с запроса на фильтр и
    сохраняет в словарь, сохраняя каждый атрибут экземпляра свойства в список,
    ключем которого есть имя каждого атрибута экземпляра свойства
    """
    properties_list = [p.split(',') for p in properties]
    dict_props = {'ids': [], 'names': [], 'text_values': [], 'numeric_values': []}
    for item in properties_list:
        cat_ids, names, text_value_prop, numeric_value_prop = item[0], item[1], item[2], Decimal(item[3])

        dict_props['ids'].append(cat_ids)
        dict_props['names'].append(names)
        dict_props['text_values'].append(text_value_prop)
        dict_props['numeric_values'].append(numeric_value_prop)

    return dict_props


def get_page_obj(per_pages: int, page: int, queryset: Union[QuerySet, list]) -> Page:
    """
    Функция принимает кол-во товаров на одной странице,
    текущую страницу и товары, которые необходимо отобразить.
    Возвращает объект страницы
    """
    p = Paginator(queryset, per_pages)

    try:
        page_obj = p.page(page)
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:  # если получен номер страницы, выходящий за общее кол-во страниц
        page_obj = p.page(p.num_pages)

    return page_obj
