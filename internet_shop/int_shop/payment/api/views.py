from functools import reduce
from operator import add

from rest_framework import status
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import OrderItem
from .serializers import PaymentSerializer
from ..views import create_checkout_session


class MakePaymentView(APIView):
    """
    API view for performing online payment
    """
    authentication_classes = [BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        content = None
        order_items = OrderItem.objects.select_related('product', 'order').filter(
            order_id=request.session['order_id']).order_by('id')
        checkout_session_response = create_checkout_session(request, *args, **kwargs)
        url = checkout_session_response.url  # the redirect url for further purchase
        order_items_copy = list(order_items.values())

        for i in range(len(order_items)):
            # save total cost of each item taking in account it quantity
            order_items_copy[i]['total_cost'] = order_items[i].get_cost()

        # calculate amount total cost for purchase
        total_purchase_cost = reduce(add, [item['total_cost'] for item in order_items_copy], 0)

        serializer = PaymentSerializer(data=order_items_copy, many=True)
        if serializer.is_valid(raise_exception=True):
            # add to content extra data along with serializer data
            content = serializer.data + [{'total_purchase_cost': total_purchase_cost, 'url': url}]

        return Response(content, status=status.HTTP_200_OK)
