from django import template
from decimal import Decimal

register = template.Library()


@register.filter(name='cut_fraction')
def cut_after_decimal_point(number: Decimal) -> str:
    """
    Фильтр проверяет, если десятичная часть содержит
    только нули, то возвращается значение без десятичной части,
    а иначе возвращается значение с десятичной частью
    """
    number_parts = str(number).split('.')
    if number_parts[1] == '00':
        return number_parts[0]
    return str(number)
