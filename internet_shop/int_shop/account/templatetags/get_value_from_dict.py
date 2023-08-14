from django import template

register = template.Library()


@register.filter('get_dict_item')
def get_item(dictionary, key):
    """
    Return value from dictionary by key
    """
    return dictionary.get(key)
