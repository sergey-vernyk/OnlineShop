from django import template

register = template.Library()


@register.filter(name='amount_dots')
def calculate_amount_dots(width: str) -> str:
    """
    Расчет кол-ва точек для вставки по все длине строки таблицы
    """
    return '.' * int((int(width) / 3.6))
