# Generated by Django 4.1.7 on 2023-03-14 16:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0010_remove_profile_present_card'),
        ('orders', '0009_order_is_email_was_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='profile',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='account.profile'),
        ),
    ]
