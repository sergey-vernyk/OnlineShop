from django import template
from decimal import Decimal

register = template.Library()


@register.filter('subtract')
def subtract(value_1: Decimal, value_2: Decimal) -> Decimal:
    """
    Return difference between two Decimal instances
    """
    return abs(value_1 - value_2)
