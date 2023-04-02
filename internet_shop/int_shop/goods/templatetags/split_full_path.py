from django import template
import re

register = template.Library()


@register.filter(name='split')
def split_full_path(request, index) -> str:
    """
    Фильтр разделяет полный путь к ресурсу
    на url для фильтра и url с запросом на поиск по фильтру
    Исходный путь - "/goods/mobile-phones/filter/1/?price_min=75.00&price_max=616.90"
    Результат - "/goods/mobile-phones/filter" "price_min=75.00&price_max=616.90"
    Возвращает результат пути по переданному индексу
    """
    path = re.split(r'/\d+/.', request.get_full_path())
    result = [f'{path[0]}', f'?{path[1]}']
    return result[index]
