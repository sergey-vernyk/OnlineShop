from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.moduls_init import redis
from orders.models import OrderItem, Order
from .serializers import PaymentSerializer
from ..views import create_checkout_session


class MakePaymentView(APIView):
    """
    Performing online payment
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        content = None
        if request.headers.get('User-Agent') == 'coreapi':
            order_id = redis.hget('order_id', f'user_id:{request.user.pk}')
        else:
            order_id = request.session['order_id']

        order = get_object_or_404(Order, id=order_id)
        order_items = OrderItem.objects.select_related('product', 'order').filter(order_id=order_id).order_by('id')
        checkout_session_response = create_checkout_session(request, *args, **kwargs)
        url = checkout_session_response.url  # the redirect url for further pay

        serializer = PaymentSerializer(data=list(order_items.values()), many=True)
        if serializer.is_valid(raise_exception=True):
            # add to content extra data along with serializer data
            content = serializer.data + [
                {'total_purchase_cost': order.get_total_values()['total_cost_with_discounts'], 'url': url}
            ]

        return Response(content, status=status.HTTP_200_OK)
