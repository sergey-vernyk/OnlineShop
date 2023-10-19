from decimal import Decimal
from typing import Union

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404, reverse, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from common.moduls_init import redis
from orders.models import Order
from .tasks import order_paid

stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET


def create_discounts(discount_type: str = None, discount_value: int = None) -> Union[stripe.Coupon, str, None]:
    """
    Creating discounts for the order: coupon or present card.
    Coupon contains with discount in percentage from total goods cost.
    Present card contains with fixed amount from total goods cost.
    """
    if not all([discount_type, discount_value]):
        return None

    discount = None

    try:
        if discount_type == 'coupon':
            discount = stripe.Coupon.create(
                percent_off=discount_value,
                duration='forever'
            )
        elif discount_type == 'present_card':
            # multiply by 100, cause convert value to cents
            discount = stripe.Coupon.create(
                amount_off=discount_value * 100,
                duration='forever',
                currency='usd'
            )

    except Exception as e:
        return str(e)

    return discount


@require_POST
@csrf_exempt
def create_checkout_session(request, *args, **kwargs) -> Union[redirect, str]:
    """
    Checkout session is customer session, when customer paying one-time purchases
    """
    if request.headers.get('User-Agent') == 'coreapi':
        order_id = redis.hget('order_id', f'user_id:{request.user.pk}')
        redis.hdel('order_id', f'user_id:{request.user.pk}')
    else:
        order_id = request.session.get('order_id')

    order = get_object_or_404(Order, pk=order_id)
    line_items = create_session_line_items(order)
    # parameters for creating checkout session
    session_params = dict(line_items=line_items,
                          mode='payment',
                          success_url=request.build_absolute_uri(reverse('payment:payment_success')),
                          cancel_url=request.build_absolute_uri(reverse('payment:payment_cancel')),
                          customer_email=request.user.email,
                          client_reference_id=order.pk)

    discount_type_value = tuple(None for _ in range(2))  # init tuple for discount parameters

    if order.coupon:
        discount_type_value = ('coupon', order.coupon.discount)
    elif order.present_card:
        discount_type_value = ('present_card', order.present_card.amount)

    discount_instance = create_discounts(*discount_type_value)  # creating coupon instance

    if discount_instance:
        session_params.update(discounts=[{'coupon': discount_instance}])  # adding discount instance

    try:
        checkout_session = stripe.checkout.Session.create(**session_params)
        request.session['stripe_checkout_session_id'] = checkout_session['id']
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)


def create_session_line_items(order: Order) -> list:
    """
    Function creates list, consists from items bought by customer
    """
    result = []

    for item in order.items.all():
        result.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': item.product.name,
                    'metadata': {'promotional': item.product.promotional, 'active': item.product.available},
                },
                'unit_amount': int(item.price * Decimal('100'))
            },
            'quantity': item.quantity,
        })

    return result


def payment_success(request):
    """
    Successfully payment view
    """
    # getting checkout session by it id and getting it payment status by order_id
    session_id = request.session['stripe_checkout_session_id']
    session = stripe.checkout.Session.retrieve(session_id)
    order_id = request.session.get('order_id')
    order = Order.objects.get(pk=order_id)

    # if order has been paid, therefore make mark it and save to DB
    if session.payment_status == 'paid':
        order.is_paid = True
        order.save(update_fields=['is_paid'])

    amount_total = (Decimal(session.amount_total or session.amount_subtotal) / Decimal('100')).quantize(Decimal('0.01'))

    return render(request, 'payment/success.html', {'amount_total': amount_total,
                                                    'order_id': session.client_reference_id})


def payment_cancel(request):
    """
    View for displaying decline payment status
    """
    order_id = request.session.get('order_id')
    return render(request, 'payment/cancel.html', {'order_id': order_id})


@require_POST
@csrf_exempt
def webhook(request) -> HttpResponse:
    """
    Webhook handling
    """
    event = None
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    # check, that request came from Stripe
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret
        )
    except ValueError:
        # invalid request content
        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError:
        # invalid signature
        return HttpResponse(status=400)

    # handling session complete event
    if event.type == 'checkout.session.completed':
        session = event.data.object
        # if the session mode is payment and the payment status is paid, send email to user, that order has been paid
        if session.mode == 'payment' and session.payment_status == 'paid':
            total_amount = (Decimal(session.amount_total or
                                    session.amount_subtotal) / Decimal('100')).quantize(Decimal('0.01'))
            order_id = session.client_reference_id  # client_reference_id corresponds order id
            order = Order.objects.get(pk=order_id)
            order.stripe_id = session.payment_intent  # assigning to the order paymentIntent id
            order.save(update_fields=['stripe_id'])

            domain = request.site.domain
            is_secure = request.is_secure()
            # sending email about order payment for the order
            order_paid.delay(data={'domain': domain, 'is_secure': is_secure},
                             order_id=order.pk,
                             amount_total=total_amount)

    return HttpResponse(status=200)
