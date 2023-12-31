# Generated by Django 4.1.7 on 2023-03-18 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0005_alter_property_charge_power_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='connection',
            field=models.CharField(blank=True, max_length=100, verbose_name='Connections'),
        ),
        migrations.AlterField(
            model_name='property',
            name='usb_type',
            field=models.CharField(blank=True, max_length=50, verbose_name='USB'),
        ),
        migrations.AlterField(
            model_name='property',
            name='wifi_type',
            field=models.CharField(blank=True, max_length=100, verbose_name='WI-FI'),
        ),
    ]
