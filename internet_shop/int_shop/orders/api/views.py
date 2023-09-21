from rest_framework import viewsets, authentication
from rest_framework.exceptions import PermissionDenied

from cart.cart import Cart
from orders.models import Order
from . import serializers
from .permissions import IsOrderOwnerOrAdmin


class OrderViewSet(viewsets.ModelViewSet):
    """
    API view allows to obtain, create, update, delete orders
    """
    queryset = Order.objects.all()
    serializer_class = serializers.OrderSerializer
    permission_classes = [IsOrderOwnerOrAdmin]
    authentication_classes = [authentication.BasicAuthentication, authentication.TokenAuthentication]

    def get_serializer_context(self):
        """
        Override for add items of the cart to the serializer context
        """
        context = super().get_serializer_context()
        cart = Cart(self.request)
        cart_items = [item for item in cart]
        context.update({'cart_items': cart_items})
        return context

    def partial_update(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied('Only staff users are able to update an order')

        return super().partial_update(request, *args, **kwargs)
