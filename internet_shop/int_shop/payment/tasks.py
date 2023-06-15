from django.conf import settings
from django.core.mail import EmailMessage
from celery import shared_task
from decimal import Decimal
from django.template.loader import render_to_string
from orders.models import Order


@shared_task
def order_paid(data: dict, order_id: int, amount_total: Decimal) -> str:
    """
    Задача отправляет сообщение на электронную почту
    пользователю, который успешно оплатил заказ
    """

    to_email = Order.objects.get(pk=order_id).email

    subject = 'Order paid'
    body = render_to_string('account/emails/order_paid_email.html',
                            {
                                'order_id': order_id,
                                'order_amount': amount_total,
                                'domain': data.get('domain'),
                                'protocol': 'https' if data.get('is_secure') else 'http',
                            })

    from_email = settings.FROM_EMAIL
    to = (str(to_email),)

    email_message = EmailMessage(subject=subject,
                                 body=body,
                                 from_email=from_email,
                                 to=to)

    email_message.content_subtype = 'html'

    status = email_message.send(fail_silently=False)
    return 'Successfully' if status else 'Not successfully'
