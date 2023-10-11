import json

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, schema
from rest_framework.response import Response

from cart.cart import Cart
from common.moduls_init import redis
from goods.models import Product
from . import serializers
from .schemas import add_or_update_cart_schema


@swagger_auto_schema(method='get', operation_summary='Get items in the cart')
@api_view(['GET'])
def cart_items(request, version: str = 'v1'):
    """
    Get follow info in response about:

    * All products in the cart
    * Total products in the cart
    * Total discount
    * Total cost with discount
    * Applied coupon or present card if any was
    """
    if request.headers.get('User-Agent') == 'coreapi':
        coupon_id = redis.hget('present_card_id', f'user_id:{request.user.pk}')
        present_card_id = redis.hget('coupon_id', f'user_id:{request.user.pk}')
        items_in_cart = redis.hget('session_cart', f'user_id:{request.user.pk}')
        request.session['cart'] = json.loads(items_in_cart) if items_in_cart else {}
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
        content.update({
            'coupon': cart.coupon.pk if cart.coupon else None,
            'present_card': cart.present_card.pk if cart.present_card else None
        })

    return Response(content, status.HTTP_200_OK)


@swagger_auto_schema(method='post',
                     operation_summary='Add product to cart with {product_id} and {quantity} or update '
                                       '{quantity} of added product with {product_id}')
@api_view(['POST'])
@schema(add_or_update_cart_schema)
def cart_add_or_update(request, product_id: int, quantity: int = 1, version: str = 'v1'):
    """
    Add product to the cart or update existed product's quantity in the cart
    """
    cart = Cart(request)
    try:
        product = Product.available_objects.get(pk=product_id)
    except ObjectDoesNotExist:
        return Response({'error': f"Product with id '{product_id}' does not exist"}, status=status.HTTP_404_NOT_FOUND)
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


@swagger_auto_schema(method='post',
                     operation_summary='Remove product with {product_id} from the cart')
@api_view(['POST'])
def cart_remove(request, product_id: int, version: str = 'v1'):
    """
    Remove product from the cart
    """
    if request.headers.get('User-Agent') == 'coreapi':
        request.session['cart'] = json.loads(redis.hget('session_cart', f'user_id:{request.user.pk}'))
        request.session.save()
        redis.hdel('session_cart', f'user_id:{request.user.pk}')
    cart = Cart(request)
    try:
        product = Product.available_objects.get(pk=product_id)
    except ObjectDoesNotExist:
        return Response({'error': f"Product with id '{product_id}' does not exist"}, status=status.HTTP_404_NOT_FOUND)
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
