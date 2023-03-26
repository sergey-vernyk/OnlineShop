from django import template
from django.http import QueryDict

register = template.Library()


@register.simple_tag(name='check_request')
def check_request(request_get: QueryDict, *args) -> bool:
    """
    Тег принимает словарь GET запроса и проверяет,
    есть ли в словаре значения, которые передаются в args
    """
    props = request_get.getlist('props')
    if props:
        props_list = [p.split(',') for p in props]
        # преобразования элементов args в строку,
        # так как в args первый элемент типа int
        if [str(arg) for arg in args] in props_list:
            return True
    return False
