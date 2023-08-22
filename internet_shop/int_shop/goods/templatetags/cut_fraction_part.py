from django import template
from decimal import Decimal

register = template.Library()


@register.filter(name='cut_fraction')
def cut_after_decimal_point(number: Decimal) -> str:
    """
    Filter checks, if after the decimal point contains only zeros,
    that's why will return value without the decimal point,
    otherwise will return value with the decimal point
    """
    number_parts = str(number).split('.')
    if number_parts[1] == '00' or number_parts[1] == '0':
        return number_parts[0]
    return str(number)
