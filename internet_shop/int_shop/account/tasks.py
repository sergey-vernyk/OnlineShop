from django.conf import settings
from django.core.mail import EmailMessage
from celery import shared_task
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from .tokens import activation_account_token
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


@shared_task
def activate_account(data: dict, user_id: int, user_email: str) -> str:
    """
    Задача для отправки сообщения новому зарегистрированному
    пользователю для подтверждения email и активации аккаунта
    """
    user = User.objects.get(pk=user_id)
    subject = 'Activate your account'
    body = render_to_string('registration/send_activation_email.html',
                            {
                                'user': user.username,
                                'email': user.email,
                                'domain': data.get('domain'),
                                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                                'token': activation_account_token.make_token(user),
                                'protocol': 'https' if data.get('is_secure') else 'http',
                            })

    email_message = EmailMessage(subject=subject,
                                 body=body,
                                 from_email=settings.FROM_EMAIL,
                                 to=(user_email,))

    email_message.content_subtype = 'html'  # добавление html контента в письмо

    status = email_message.send(fail_silently=False)
    return 'Successfully' if status else 'Not successfully'
