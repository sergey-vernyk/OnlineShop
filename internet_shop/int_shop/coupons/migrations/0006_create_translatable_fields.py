# Generated by Django 4.1.9 on 2023-10-26 12:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coupons', '0005_create_translatable_fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ('id',), 'verbose_name': 'Category', 'verbose_name_plural': 'Categories'},
        ),
    ]
