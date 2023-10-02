import json

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, authentication, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from account.api.permissions import IsTheSameUserThatMakesAction
from account.models import Profile
from cart.cart import Cart
from common.moduls_init import redis
from orders.models import Order, Delivery
from . import serializers
from .permissions import IsOrderOwnerOrAdmin
from .schemas import get_deliveries_by_user_schema, OrderSchema, get_orders_by_user_schema


class OrderViewSet(viewsets.ModelViewSet):
    """
    API view allows to obtain, create, update, delete orders
    """
    queryset = Order.objects.all()
    serializer_class = serializers.OrderSerializer
    permission_classes = [IsOrderOwnerOrAdmin]
    authentication_classes = [authentication.BasicAuthentication, authentication.TokenAuthentication]
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

    @action(methods=['POST'],
            detail=False,
            url_path=r'user_orders/(?P<username>[a-zA-Z-_]+)/?',
            url_name='orders_by_user',
            permission_classes=[IsTheSameUserThatMakesAction, IsAdminUser],
            schema=get_orders_by_user_schema)
    def get_orders_by_user(self, request, username: str):
        """
        Action returns orders by passed username
        """
        current_profile = get_object_or_404(Profile, user__username=username)
        self.check_object_permissions(request, current_profile)
        profile_orders = Order.objects.only('first_name').filter(profile=current_profile)
        serializer = self.get_serializer(instance=profile_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeliveryViewSet(viewsets.ModelViewSet):
    """
    API view allows to obtain, create, update, delete delivery
    """
    queryset = Delivery.objects.select_related('order')
    permission_classes = [IsAdminUser]
    authentication_classes = [authentication.BasicAuthentication, authentication.TokenAuthentication]
    serializer_class = serializers.DeliverySerializer

    @action(methods=['POST'],
            detail=False,
            url_path=r'user_deliveries/(?P<username>[a-zA-Z-_]+)/?',
            url_name='deliveries_by_user',
            schema=get_deliveries_by_user_schema,
            permission_classes=[IsTheSameUserThatMakesAction, IsAdminUser])
    def get_deliveries_by_user(self, request, username: str):
        """
        Action returns deliveries by passed username
        """
        current_profile = get_object_or_404(Profile, user__username=username)
        self.check_object_permissions(request, current_profile)
        profile_orders = Order.objects.select_related('delivery').filter(profile=current_profile)
        delivery_info = Delivery.objects.filter(order__id__in=[order.pk for order in profile_orders])
        serializer = self.get_serializer(instance=delivery_info, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
