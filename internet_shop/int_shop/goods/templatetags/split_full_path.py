from django import template
import re

register = template.Library()


@register.filter(name='split')
def split_full_path(request, index) -> str:
    """
    Filter splits full path to the resource into the URL for the filter,
    and the URL with the filter request.
    Initial path - "/goods/mobile-phones/filter/1/?price_min=75.00&price_max=616.90"
    Result - "/goods/mobile-phones/filter" "price_min=75.00&price_max=616.90"
    Returns path result by received index
    """
    path = re.split(r'/\d+/.', request.get_full_path())
    result = [f'{path[0]}', f'?{path[1]}']
    return result[index]
