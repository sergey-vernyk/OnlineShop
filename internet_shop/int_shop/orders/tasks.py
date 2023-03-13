from django.conf import settings
from django.core.mail import EmailMessage
from celery import shared_task
from django.contrib.auth.models import User


@shared_task
def order_created(order_id: int, user_id: int) -> str:
    """
    Задача отправляет сообщение на электронную почту
    пользователю, который сделал заказ
    и заказ был успешно создан и подтвержден
    """
    to_email = User.objects.get(pk=user_id).email

    subject = 'Order confirmed'
    body = f'Thanks for your order! ' \
           f'Your order ID is {order_id}\n' \
           f'Our manager contact you within 10 minutes'
    from_email = settings.FROM_EMAIL
    to = (str(to_email),)

    email_message = EmailMessage(subject=subject,
                                 body=body,
                                 from_email=from_email,
                                 to=to)
    status = email_message.send(fail_silently=False)
    return 'Successfully' if status else 'Not successfully'
