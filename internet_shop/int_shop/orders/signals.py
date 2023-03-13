from django.db.models.signals import pre_save
from django.dispatch import receiver
from celery.result import AsyncResult

from orders.models import Order


# @receiver(pre_save, sender=Order)
# def check_status_email_send_task(*args,**kwargs):
#     print('Signals call')
#
#     result = AsyncResult(kwargs['status_id'])
#     if result.result == 'Successfully':
#         kwargs['instance'].is_email_was_sent = True
