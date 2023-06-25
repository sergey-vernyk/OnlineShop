from typing import Union, Generator, Tuple
import redis
from django.conf import settings
from django.db.models import QuerySet
from decimal import Decimal
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page

from goods.models import Manufacturer, Product

# инициализация Redis
r = redis.Redis(host=settings.REDIS_DB_HOST,
                port=settings.REDIS_DB_PORT,
                db=settings.REDIS_DB_NUM,
                username=settings.REDIS_DB_USER,
                password=settings.REDIS_DB_PASSWORD)


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


def get_collections_with_manufacturers_info(qs: QuerySet) -> Generator[Union[QuerySet, dict], None, None]:
    """
    Функция возвращает объекты генераторов,
    которые содержат queryset с производителями для полученного qs из товаров
    и словарь с кол-вом товаров для каждого производителя
    """
    manufacturers = Manufacturer.objects.filter(
        id__in=(item['manufacturer_id'] for item in qs.values('manufacturer_id'))
    )
    yield manufacturers

    manufacturers_prod_qnty = {}
    for p in qs.select_related('manufacturer'):
        manufacturers_prod_qnty[p.manufacturer.name] = manufacturers_prod_qnty.get(p.manufacturer.name, 0) + 1

    yield manufacturers_prod_qnty


def get_products_sorted_by_views(list_ids: list) -> Tuple[list, dict]:
    """
    Функция возвращает кортеж со списком с id товаров,
    которые отсортированы по кол-ву их просмотров
    и словарем с этими товарами
    """
    # получение всех товаров и связанных с ними категорий и сортировка их по id
    products = Product.objects.select_related('category').filter(id__in=list_ids).order_by('pk')
    # словарь с ключами id товара и значениями кол-ва его просмотров и категории товара
    # {pk: {views: int, category: str}}
    products_views = {}
    for product in products:
        products_views[product.pk] = {
            'views': int(r.hget(f'product_id:{product.pk}', 'views') or 0),
            'category': product.category.slug
        }

    # сортировка словаря по уменьшению кол-ва просмотров
    products_views_sorted = {
        pk: {'views': data['views'], 'category': data['category']}
        for pk, data in sorted(products_views.items(), key=lambda x: x[1]['views'], reverse=True)
    }

    products_ids_sorted = [pk for pk in products_views_sorted.keys()]  # ключи отсортированных товаров
    # словарь с отсортированными товарами по кол-ву просмотров
    products = Product.objects.select_related('category').in_bulk(products_ids_sorted)

    return products_ids_sorted, products
