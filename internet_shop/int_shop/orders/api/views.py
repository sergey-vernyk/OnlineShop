import json

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


class OrderViewSet(viewsets.ModelViewSet):
    """
    Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` actions.

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
        cart_items = [item for item in cart]
        context.update({'cart_items': cart_items})
        return context

    def partial_update(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied('Only staff users are able to update an order')

        return super().partial_update(request, *args, **kwargs)

    @action(methods=['GET'],
            detail=False,
            url_path='me',
            url_name='orders_by_user',
            permission_classes=[IsAuthenticated],
            schema=get_orders_by_user_schema)
    def get_orders_by_user(self, request):
        """
        Returns orders o current profile
        """
        current_profile = Profile.objects.get(user=request.user)
        profile_orders = Order.objects.prefetch_related('items', 'items__product').filter(profile=current_profile)
        serializer = self.get_serializer(instance=profile_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeliveryViewSet(viewsets.ModelViewSet):
    """
    Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` actions.

    * get - obtain all deliveries
    * post - create new delivery
    * get/{id} - retrieve order with `id`
    * patch/{id} - update one or several fields of delivery with `id`
    * delete/{id} - delete delivery with `id`
    """
    queryset = Delivery.objects.select_related('order')
    permission_classes = [IsAdminUser]
    serializer_class = serializers.DeliverySerializer

    @action(methods=['GET'],
            detail=False,
            url_path='me',
            url_name='deliveries_by_user',
            schema=get_deliveries_by_user_schema,
            permission_classes=[IsAuthenticated])
    def get_deliveries_by_user(self, request):
        """
        Returns deliveries of current profile
        """
        current_profile = Profile.objects.get(user=request.user)
        profile_orders = Order.objects.select_related('delivery').filter(profile=current_profile)
        delivery_info = Delivery.objects.filter(order__id__in=[order.pk for order in profile_orders])
        serializer = self.get_serializer(instance=delivery_info, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
