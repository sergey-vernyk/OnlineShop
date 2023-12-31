# Generated by Django 4.1.7 on 2023-03-18 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0004_alter_manufacturer_options_alter_manufacturer_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='charge_power',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, verbose_name='Power Charge'),
        ),
        migrations.AlterField(
            model_name='property',
            name='connection',
            field=models.CharField(blank=True, max_length=10, verbose_name='Connections'),
        ),
        migrations.AlterField(
            model_name='property',
            name='cpu',
            field=models.CharField(blank=True, max_length=50, verbose_name='CPU model'),
        ),
        migrations.AlterField(
            model_name='property',
            name='graphics_type',
            field=models.CharField(blank=True, max_length=30, verbose_name='Graphic Type'),
        ),
        migrations.AlterField(
            model_name='property',
            name='hdmi',
            field=models.CharField(blank=True, max_length=20, verbose_name='HDMI'),
        ),
        migrations.AlterField(
            model_name='property',
            name='ram_type',
            field=models.CharField(blank=True, max_length=20, verbose_name='RAM Type'),
        ),
        migrations.AlterField(
            model_name='property',
            name='rom_type',
            field=models.CharField(blank=True, max_length=30, verbose_name='ROM Type'),
        ),
        migrations.AlterField(
            model_name='property',
            name='rom_value',
            field=models.CharField(blank=True, max_length=20, verbose_name='ROM Capacity'),
        ),
        migrations.AlterField(
            model_name='property',
            name='screen_diagonal',
            field=models.CharField(blank=True, max_length=20, verbose_name='Screen Diagonal'),
        ),
        migrations.AlterField(
            model_name='property',
            name='screen_resolution',
            field=models.CharField(blank=True, max_length=20, verbose_name='Screen Resolution'),
        ),
        migrations.AlterField(
            model_name='property',
            name='screen_type',
            field=models.CharField(blank=True, max_length=20, verbose_name='Scree Type'),
        ),
        migrations.AlterField(
            model_name='property',
            name='usb_type',
            field=models.CharField(blank=True, max_length=30, verbose_name='USB'),
        ),
        migrations.AlterField(
            model_name='property',
            name='wifi_type',
            field=models.CharField(blank=True, max_length=50, verbose_name='WI-FI'),
        ),
        migrations.AlterField(
            model_name='property',
            name='work_time',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=6, verbose_name='Working time, Hours'),
        ),
    ]
