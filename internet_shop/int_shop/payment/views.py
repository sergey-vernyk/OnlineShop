from django.shortcuts import redirect, get_object_or_404, reverse, render
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal

from orders.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def create_checkout_session(request):
    """
    Сеанс оформления заказа представляет собой сеанс клиента,
    когда он оплачивает разовые покупки
    """
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, pk=order_id)
    line_items = create_session_line_items(order)

    if request.method == 'POST':
        # пытаемся создать сессию
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri(reverse('payment:payment_success')),  # полный путь с доменом
                cancel_url=request.build_absolute_uri(reverse('payment:payment_cancel')),
                customer_email=request.user.email,
                client_reference_id=order.pk,
            )
        except Exception as e:
            return str(e)

        return redirect(checkout_session.url, code=303)
    else:
        return render(request, 'payment/checkout.html')


def create_session_line_items(order: Order) -> list:
    """
    Функция создает список с позициями, купленными покупателем
    """
    result = []

    for item in order.items.all():
        result.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': item.product.name},
                'unit_amount': int(item.price * Decimal('100'))},
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
        order.save()

    return render(request, 'payment/success.html')


def payment_cancel(request):
    """
    Представление отклонения оплаты
    """
    return render(request, 'payment/cancel.html')
