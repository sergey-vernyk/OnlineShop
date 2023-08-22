from django import template
from django.http import QueryDict

register = template.Library()


@register.simple_tag(name='check_request')
def check_request(request_get: QueryDict, *args) -> bool:
    """
    Tag receives GET dict and checks, whether values are in the dict, that passed in args
    """
    props = request_get.getlist('props')
    if props:
        props_list = [p.split(',') for p in props]
        # convert args elements in string,
        # because first element is the int type
        if [str(arg) for arg in args] in props_list:
            return True
    return False
