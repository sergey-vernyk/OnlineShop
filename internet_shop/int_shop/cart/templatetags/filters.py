from decimal import Decimal
from typing import Union

from django import template
from decimal import InvalidOperation

register = template.Library()


@register.filter('multiply')
def multiply(value1, value2) -> Union[Decimal, None]:
    """
    Фильтр возвращает результат перемножения значений
    """
    try:
        result = Decimal(value1) * Decimal(value2)
    except InvalidOperation:
        return None
    else:
        return result


@register.filter('to_str')
def to_str(arg: int) -> str:
    """
    Фильтр возвращает строку,
    конвертированную из числа
    """
    return str(arg)
