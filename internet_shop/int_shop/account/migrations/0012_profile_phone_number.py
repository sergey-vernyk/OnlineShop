# Generated by Django 4.1.7 on 2023-04-14 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0011_profile_email_confirm'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='phone_number',
            field=models.CharField(blank=True, max_length=15),
        ),
    ]
