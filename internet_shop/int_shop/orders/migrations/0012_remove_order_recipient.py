# Generated by Django 4.1.7 on 2023-04-23 15:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_order_is_done'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='recipient',
        ),
    ]