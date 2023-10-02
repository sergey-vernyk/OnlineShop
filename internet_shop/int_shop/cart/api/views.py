import json

from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status, parsers, authentication
from rest_framework.decorators import api_view, parser_classes, authentication_classes, schema
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from cart.cart import Cart
from common.moduls_init import redis
from goods.models import Product
from . import serializers
from .schemas import add_update_cart_schema


@api_view(['GET'])
@parser_classes([parsers.JSONParser])
@authentication_classes([authentication.TokenAuthentication, authentication.BasicAuthentication])
def cart_items_view(request):
    """
    API allows to obtain all products in the cart and info about total products in the cart,
    total discount, total cost with discount, and coupon or present card if they exists
    """
    if request.headers.get('User-Agent') == 'coreapi':
        coupon_id = redis.hget('present_card_id', f'user_id:{request.user.pk}')
        present_card_id = redis.hget('coupon_id', f'user_id:{request.user.pk}')
        cart_items = redis.hget('session_cart', f'user_id:{request.user.pk}')
        request.session['cart'] = json.loads(cart_items) if cart_items else {}
        request.session['present_card_id'] = None if not coupon_id else int(coupon_id)
        request.session['coupon_id'] = None if not present_card_id else int(present_card_id)
        request.session.save()

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
@schema(add_update_cart_schema)
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
        # since while using CoreAPI the session is not saving, we need to save cart with items in redis
        if request.headers.get('User-Agent') == 'coreapi':
            cart_as_bytes = json.dumps(request.session['cart']).encode('utf-8')
            redis.hset('session_cart', f'user_id:{request.user.pk}', cart_as_bytes)
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
    if request.headers.get('User-Agent') == 'coreapi':
        request.session['cart'] = json.loads(redis.hget('session_cart', f'user_id:{request.user.pk}'))
        request.session.save()
        redis.hdel('session_cart', f'user_id:{request.user.pk}')
    cart = Cart(request)
    try:
        product = get_object_or_404(Product, pk=product_id)
    except Http404 as e:
        raise NotFound(e)
    else:
        cart.remove(product_id)
        if not cart:
            if request.headers.get('User-Agent') == 'coreapi':
                if redis.hexists('coupon_id', f'user_id:{request.user.pk}'):
                    redis.hdel('coupon_id', f'user_id:{request.user.pk}')
                elif redis.hexists('present_card_id', f'user_id:{request.user.pk}'):
                    redis.hdel('present_card_id', f'user_id:{request.user.pk}')
            else:
                cart.clear()
        return Response(
            {'success': f'Product {product.name} with id {product.pk} has been successfully removed'},
            status=status.HTTP_200_OK
        )
