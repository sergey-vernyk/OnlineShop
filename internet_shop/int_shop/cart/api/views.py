from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, schema
from rest_framework.response import Response

from cart.cart import Cart
from goods.models import Product
from . import serializers
from .schemas import add_or_update_cart_schema
from .utils import show_cart_content_coreapi, remove_cart_content_coreapi, add_cart_content_coreapi


@swagger_auto_schema(method='get', operation_summary='Get items in the cart')
@api_view(['GET'])
def cart_items(request, version: str = 'v1') -> Response:
    """
    Get follow info in response about:

    * All products in the cart.
    * Total products in the cart.
    * Total discount.
    * Total cost with discount.
    * Applied coupon or present card if any was.
    """

    cart = Cart(request)

    if request.headers.get('User-Agent') == 'coreapi':
        cart = show_cart_content_coreapi(cart, request.user.pk)

    serializer = serializers.CartSerializer(instance=list(cart), many=True)
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
def cart_add_or_update(request, product_id: int, quantity: int = 1, version: str = 'v1') -> Response:
    """
    Add product to the cart or update existed product's quantity in the cart.
    """

    try:
        product = Product.available_objects.get(pk=product_id)
    except ObjectDoesNotExist:
        return Response({'error': f"Product with id '{product_id}' does not exist"}, status=status.HTTP_404_NOT_FOUND)

    cart = Cart(request)

    if request.headers.get('User-Agent') == 'coreapi':
        add_cart_content_coreapi(cart, request.user.pk, product, quantity)

    cart.add(product, int(quantity))
    return Response(
        {'success': f'Product {product.name} with id {product.pk} has been successfully'
                    f' added or updated it quantity to {quantity}'},
        status=status.HTTP_200_OK
    )


@swagger_auto_schema(method='post',
                     operation_summary='Remove product with {product_id} from the cart')
@api_view(['POST'])
def cart_remove(request, product_id: int, version: str = 'v1') -> Response:
    """
    Remove product from the cart.
    """

    try:
        product = Product.available_objects.get(pk=product_id)
    except ObjectDoesNotExist:
        return Response({'error': f"Product with id '{product_id}' does not exist"}, status=status.HTTP_404_NOT_FOUND)

    cart = Cart(request)

    if request.headers.get('User-Agent') == 'coreapi':
        remove_cart_content_coreapi(cart, request.user.pk, product_id)
    cart.remove(product_id)
    if not cart:
        cart.clear()
    return Response(
        {'success': f'Product {product.name} with id {product.pk} has been successfully removed'},
        status=status.HTTP_200_OK
    )
