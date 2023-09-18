from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status, parsers, authentication
from rest_framework.decorators import api_view, parser_classes, authentication_classes
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from cart.cart import Cart
from goods.models import Product
from . import serializers


@api_view(['GET'])
@parser_classes([parsers.JSONParser])
@authentication_classes([authentication.TokenAuthentication, authentication.BasicAuthentication])
def cart_items_view(request):
    """
    API allows to obtain all products in the cart and info about total products in the cart,
    total discount, total cost with discount, and coupon or present card if they exists
    """
    cart = Cart(request)
    serializer = serializers.CartSerializer(instance=[item for item in cart], many=True)
    total_products = cart.get_amount_items_in()
    total_cost_with_discounts = cart.get_total_price_with_discounts()
    total_discount = cart.get_total_discount()
    content = {
        'items': serializer.data,
        'total_items': total_products,
        'total_cost_with_discounts': total_cost_with_discounts,
        'total_discount': total_discount,
    }

    # allow to see what coupon or present card was applied if any
    if not isinstance(request.user, AnonymousUser):
        content.update(
            {'coupon': cart.coupon.pk if cart.coupon else None,
             'present_card': cart.present_card.pk if cart.present_card else None}
        )

    return Response(content, status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([authentication.TokenAuthentication, authentication.BasicAuthentication])
def cart_add_or_update(request, product_id: int, quantity: int = 1):
    """
    API view allows to add product to cart
    """
    cart = Cart(request)
    try:
        product = get_object_or_404(Product, pk=product_id)
    except Http404 as e:
        raise NotFound(e)
    else:
        cart.add(product, int(quantity))
        return Response(
            {'success': f'Product {product.name} with id {product.pk} has been successfully'
                        f' added or updated it quantity to {quantity}'},
            status=status.HTTP_200_OK
        )


@api_view(['POST'])
@authentication_classes([authentication.TokenAuthentication, authentication.BasicAuthentication])
def cart_remove(request, product_id: int):
    """
    API view allows to remove product from cart
    """
    cart = Cart(request)
    try:
        product = get_object_or_404(Product, pk=product_id)
    except Http404 as e:
        raise NotFound(e)
    else:
        cart.remove(product_id)
        return Response(
            {'success': f'Product {product.name} with id {product.pk} has been successfully removed'},
            status=status.HTTP_200_OK
        )
