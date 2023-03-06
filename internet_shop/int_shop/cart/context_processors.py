from .cart import Cart


def cart(request):
    """
    Метод делает корзину доступной во всех шаблонах
    """
    return {'cart': Cart(request)}
