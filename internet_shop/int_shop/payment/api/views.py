from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
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
    Performing online payment.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary='Performing online payment if order has been successfully completed',
                         responses={'400': 'Order issues', '200': 'Payment has been successfully completed'})
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        content = None
        if request.headers.get('User-Agent') == 'coreapi':
            order_id = redis.hget('order_id', f'user_id:{request.user.pk}')
        else:
            order_id = request.session.get('order_id')

        if not order_id:
            return Response({'error': 'You must make order first and than you will can make a payment'},
                            status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, id=order_id)

        if order.pay_method != 'Online':
            return Response({'error': 'Order pay method must be `Online` to make online payment'},
                            status=status.HTTP_400_BAD_REQUEST)

        order_items = OrderItem.objects.select_related('product', 'order').filter(order_id=order_id).order_by('id')
        checkout_session_response = create_checkout_session(request, *args, **kwargs)
        url = checkout_session_response.url  # the redirect url for further pay

        serializer = PaymentSerializer(data=list(order_items.values()), many=True)
        if serializer.is_valid(raise_exception=True):
            total_values = order.get_total_values()
            # add to content extra data along with serializer data
            content = serializer.data + [
                {
                    'total_purchase_cost': total_values['total_cost_with_discounts'] or total_values['total_cost'],
                    'url': url
                }
            ]

        return Response(content, status=status.HTTP_200_OK)
