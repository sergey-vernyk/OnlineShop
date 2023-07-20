from typing import Union

from django.shortcuts import redirect, get_object_or_404, reverse, render
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from orders.models import Order
from .tasks import order_paid

stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET


def create_discounts(discount_type: str = None, discount_value: int = None) -> Union[stripe.Coupon, str, None]:
    """
    Создание скидок для оплаты: купон или подарочная карта.
    Купон содержит скидку в процентах от полной суммы за товары.
    Подарочная карта содержит фиксированную сумму от полной суммы за товары.
    """
    if not (discount_type and discount_value):
        return None

    discount = None

    try:
        if discount_type == 'coupon':
            discount = stripe.Coupon.create(
                percent_off=discount_value,
                duration='forever'
            )
        elif discount_type == 'present_card':
            # умножение на 100 для перевода значения в центы
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
def create_checkout_session(request) -> Union[redirect, str]:
    """
    Сеанс оформления заказа представляет собой сеанс клиента,
    когда он оплачивает разовые покупки
    """
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, pk=order_id)
    line_items = create_session_line_items(order)
    # параметры для создания CheckoutSession
    session_params = dict(line_items=line_items,
                          mode='payment',
                          success_url=request.build_absolute_uri(reverse('payment:payment_success')),
                          cancel_url=request.build_absolute_uri(reverse('payment:payment_cancel')),
                          customer_email=request.user.email,
                          client_reference_id=order.pk)

    discount_type_value = tuple(None for _ in range(2))  # начальная инициализация кортежа для параметров скидки

    if order.coupon:
        discount_type_value = ('coupon', order.coupon.discount)
    if order.present_card:
        discount_type_value = ('present_card', order.present_card.amount)

    discount_instance = create_discounts(*discount_type_value)  # создание экземпляра купона

    if discount_instance:
        session_params.update(discounts=[{'coupon': discount_instance}])  # добавление экземпляра скидки

    try:
        checkout_session = stripe.checkout.Session.create(**session_params)
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)


def create_session_line_items(order: Order) -> list:
    """
    Функция создает список с позициями, купленными покупателем
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
    Представление успешного завершения оплаты
    """
    # достаем сессию по её id и смотрим статус оплаты заказа с order_id
    session_id = stripe.checkout.Session.list().data[0].stripe_id
    session = stripe.checkout.Session.retrieve(session_id)
    order_id = request.session.get('order_id')
    order = Order.objects.get(pk=order_id)

    # если заказ был оплачен - обозначаем это и сохраняем
    if session.payment_status == 'paid':
        order.is_paid = True
        order.save(update_fields=['is_paid'])

    amount_total = (Decimal(session.amount_total or session.amount_subtotal) / Decimal('100')).quantize(Decimal('0.01'))

    return render(request, 'payment/success.html', {'amount_total': amount_total,
                                                    'order_id': session.client_reference_id})


def payment_cancel(request):
    """
    Представление отклонения оплаты
    """
    return render(request, 'payment/cancel.html')


@require_POST
@csrf_exempt
def webhook(request) -> HttpResponse:
    """
    Обработка вебхука
    """
    event = None
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    # проверка, что запрос пришел от Stripe
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret
        )
    except ValueError:
        # невалидный содержание запроса
        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError:
        # невалидная сигнатура
        return HttpResponse(status=400)

    # обработка события завершения сессии
    if event.type == 'checkout.session.completed':
        session = event.data.object
        # если режим сессии оплата и статус оплачено - отправка email пользователю, что заказ был оплачен
        if session.mode == 'payment' and session.payment_status == 'paid':
            total_amount = (Decimal(session.amount_total or
                                    session.amount_subtotal) / Decimal('100')).quantize(Decimal('0.01'))
            order_id = session.client_reference_id  # client_reference_id соответствует id заказа
            order = Order.objects.get(pk=order_id)
            order.stripe_id = session.payment_intent  # присвоение заказу id paymentIntent
            order.save(update_fields=['stripe_id'])

            domain = request.site.domain
            is_secure = request.is_secure()
            # отправка email об оплате заказа
            order_paid.delay(data={'domain': domain, 'is_secure': is_secure},
                             order_id=order.pk,
                             amount_total=total_amount)

    return HttpResponse(status=200)
