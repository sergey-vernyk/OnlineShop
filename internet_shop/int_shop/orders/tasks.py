from django.conf import settings
from django.core.mail import EmailMessage
from celery import shared_task
from django.template.loader import render_to_string
from orders.models import Order


@shared_task
def order_created(data: dict, order_id: int, profile_username: str) -> str:
    """
    Задача отправляет сообщение на электронную почту
    пользователю, который сделал заказ
    и заказ был успешно создан и подтвержден
    """
    order = Order.objects.get(pk=order_id)
    order_totals = order.get_total_values()

    subject = 'Order confirmed'
    body = render_to_string('account/emails/order_created_email.html',
                            {
                                'order_id': order_id,
                                'order_amount': order_totals['total_cost_with_discounts'] or order_totals['total_cost'],
                                'domain': data.get('domain'),
                                'protocol': 'https' if data.get('is_secure') else 'http',
                                'username': profile_username,
                            })

    from_email = settings.FROM_EMAIL
    to = (str(order.email),)

    email_message = EmailMessage(subject=subject,
                                 body=body,
                                 from_email=from_email,
                                 to=to)

    email_message.content_subtype = 'html'

    status = email_message.send(fail_silently=False)
    return 'Successfully' if status else 'Not successfully'
