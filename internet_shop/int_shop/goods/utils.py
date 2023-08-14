from decimal import Decimal
from typing import Union, Generator, Tuple

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page
from django.db.models import QuerySet

from common.moduls_init import redis
from goods.models import Manufacturer, Product


def distribute_properties_from_request(properties: list) -> dict:
    """
    Function gathers all received properties from request on filter,
    save to the dictionary in which key is the name of the property instance attribute,
    and value is the list with this instance property attribute values
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
    Function returns page object
    per_pages -> number of products per page;
    page -> current page;
    queryset -> list of the products, which have to display on all pages
    """
    p = Paginator(queryset, per_pages)

    try:
        page_obj = p.page(page)
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:  # if received page number grater than amount pages
        page_obj = p.page(p.num_pages)

    return page_obj


def get_collections_with_manufacturers_info(qs: QuerySet) -> Generator[Union[QuerySet, dict], None, None]:
    """
    Function returns generator objects, which contains queryset with the manufacturers
    for received queryset with products and the dictionary with quantity of products for each manufacturer
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
    Function returns tuple with list, that contains products ids,
    which are sorted by amount views and contains dictionary with these products
    """
    # getting all products, which linked with categories and then sort their by id
    products = Product.objects.select_related('category').filter(id__in=list_ids).order_by('pk')
    # dictionary with keys as product id and value as a dictionary with views quantity and product category
    # {pk: {views: int, category: str}}
    products_views = {}
    for product in products:
        products_views[product.pk] = {
            'views': int(redis.hget(f'product_id:{product.pk}', 'views') or 0),
            'category': product.category.slug
        }

    # dict sort by descending of views numbers
    products_views_sorted = {
        pk: {'views': data['views'], 'category': data['category']}
        for pk, data in sorted(products_views.items(), key=lambda x: x[1]['views'], reverse=True)
    }

    products_ids_sorted = [pk for pk in products_views_sorted.keys()]  # the keys of sorted products
    # dict with the sorted products by number of views
    products = Product.objects.select_related('category').in_bulk(products_ids_sorted)

    return products_ids_sorted, products
