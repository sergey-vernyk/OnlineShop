from .cart import Cart


def cart(request):
    """
    Making cart available in all templates
    """
    return {'cart': Cart(request)}
