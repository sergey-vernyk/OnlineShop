from django import template

register = template.Library()


@register.filter('get_dict_item')
def get_item(dictionary, key):
    """
    Возврат значения из словаря dictionary по ключу key
    """
    return dictionary.get(key)
