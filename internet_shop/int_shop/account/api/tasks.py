from celery import shared_task
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth.models import User


@shared_task
def send_email_for_set_new_account_password(uidb64, token, email, username, is_secure, domain):
    """
    Task for sending email to user email with instruction about set new password after reset
    """
    user = User.objects.get(username=username)
    subject = 'Reset your forgot password'
    body = render_to_string('password_reset_email_html_api.html',
                            {
                                'uid': uidb64,
                                'token': token,
                                'email': email,
                                'user': user,
                                'protocol': 'https' if is_secure else 'http',
                                'domain': domain
                            })

    email_message = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.FROM_EMAIL,
        to=(email,)
    )

    email_message.content_subtype = 'html'  # add html content to the email

    status = email_message.send(fail_silently=False)
    return 'Successfully' if status else 'Not successfully'
