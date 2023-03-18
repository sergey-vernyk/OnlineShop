from django.conf import settings
from django.core.mail import EmailMessage
from celery import shared_task
from decimal import Decimal

from orders.models import Order


@shared_task
def order_paid(order_id: int, total_amount: int) -> str:
    """
    Задача отправляет сообщение на электронную почту
    пользователю, который успешно оплатил заказ
    """

    to_email = Order.objects.get(pk=order_id).email

    subject = 'Order paid'
    body = (f'Thanks for your payment! '
            f'Your payment amount is ${Decimal(str(total_amount)) / Decimal("100")}. '
            f'Your order ID is {order_id}\n')

    from_email = settings.FROM_EMAIL
    to = (str(to_email),)

    email_message = EmailMessage(subject=subject,
                                 body=body,
                                 from_email=from_email,
                                 to=to)
    status = email_message.send(fail_silently=False)
    return 'Successfully' if status else 'Not successfully'
