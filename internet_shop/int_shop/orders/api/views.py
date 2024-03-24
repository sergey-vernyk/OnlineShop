import json

from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from account.models import Profile
from cart.cart import Cart
from common.moduls_init import redis
from orders.models import Order, Delivery
from . import serializers
from .permissions import UserPermission
from .schemas import get_deliveries_by_user_schema, OrderSchema, get_orders_by_user_schema


@method_decorator(name='create',
                  decorator=swagger_auto_schema(operation_summary='Create an order'))
@method_decorator(name='list',
                  decorator=swagger_auto_schema(operation_summary='Get all orders'))
@method_decorator(name='retrieve',
                  decorator=swagger_auto_schema(operation_summary='Get order with {id}'))
@method_decorator(name='destroy',
                  decorator=swagger_auto_schema(operation_summary='Delete order with {id}'))
class OrderViewSet(viewsets.ModelViewSet):
    """
    Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` orders.

    * get - obtain all orders
    * post - create new order
    * get/{id} - retrieve order with `id`
    * patch/{id} - update one or several fields of order with `id`
    * delete/{id} - delete order with `id`
    """
    queryset = Order.objects.prefetch_related('items', 'items__product', 'delivery')
    serializer_class = serializers.OrderSerializer
    permission_classes = [UserPermission]
    schema = OrderSchema()
    http_method_names = ['get', 'head', 'post', 'patch', 'delete']

    def get_serializer_context(self):
        """
        Override for add items of the cart to the serializer context
        """
        context = super().get_serializer_context()
        if self.request.headers.get('User-Agent') == 'coreapi':
            self.request.session['cart'] = json.loads(
                redis.hget('session_cart', f'user_id:{self.request.user.pk}') or b'{}')
            self.request.session.save()
        cart = Cart(self.request)
        context.update({'cart_items': list(cart)})
        return context

    @swagger_auto_schema(operation_summary='Update one or more order\'s field(s) with {id}')
    def partial_update(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied('Only staff users are able to update an order')

        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(method='get', operation_summary='Get all current user\'s orders')
    @action(methods=['GET'],
            detail=False,
            url_path='me',
            url_name='current_user_orders',
            permission_classes=[IsAuthenticated])
    def get_current_user_orders(self, request, version: str = 'v1'):
        """
        Returns orders of current profile.
        """
        current_profile = Profile.objects.get(user=request.user)
        profile_orders = Order.objects.prefetch_related('items', 'items__product').filter(profile=current_profile)
        serializer = self.get_serializer(instance=profile_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(method='get', operation_summary='Get all orders of user with {username}')
    @action(methods=['GET'],
            detail=False,
            url_path=r'(?P<username>[a-zA-z-_]+)',
            url_name='orders_by_username',
            permission_classes=[IsAdminUser],
            schema=get_orders_by_user_schema)
    def get_orders_by_username(self, request, username: str, version: str = 'v1'):
        profile = Profile.objects.get(user__username=username)
        profile_orders = Order.objects.prefetch_related('items', 'items__product').filter(profile=profile)
        serializer = self.get_serializer(instance=profile_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@method_decorator(name='list',
                  decorator=swagger_auto_schema(operation_summary='Get all deliveries'))
@method_decorator(name='retrieve',
                  decorator=swagger_auto_schema(operation_summary='Get delivery with {id}'))
@method_decorator(name='destroy',
                  decorator=swagger_auto_schema(operation_summary='Delete delivery with {id}'))
@method_decorator(name='partial_update',
                  decorator=swagger_auto_schema(operation_summary='Update one or more delivery\'s field(s) with {id}'))
class DeliveryViewSet(viewsets.ModelViewSet):
    """
    Viewset that provides `retrieve`, `delete`, `list` and `update` deliveries.

    * get - obtain all deliveries
    * get/{id} - retrieve order with `id`
    * patch/{id} - update one or several fields of delivery with `id`
    * delete/{id} - delete delivery with `id`
    """
    queryset = Delivery.objects.select_related('order')
    permission_classes = [IsAdminUser]
    serializer_class = serializers.DeliverySerializer
    http_method_names = ['get', 'head', 'patch', 'delete']

    @swagger_auto_schema(method='get', operation_summary='Get all deliveries of user with {username}')
    @action(methods=['GET'],
            detail=False,
            url_path='(?P<username>[a-zA-z-_]+)',
            url_name='deliveries_by_username',
            schema=get_deliveries_by_user_schema,
            permission_classes=[IsAdminUser])
    def get_deliveries_by_username(self, request, username: str, version: str = 'v1'):
        """
        Returns deliveries of current profile
        """
        profile = Profile.objects.get(user__username=username)
        profile_orders = Order.objects.select_related('delivery').filter(profile=profile)
        delivery_info = Delivery.objects.filter(order__id__in=[order.pk for order in profile_orders])
        serializer = self.get_serializer(instance=delivery_info, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
