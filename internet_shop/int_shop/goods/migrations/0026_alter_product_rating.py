# Generated by Django 4.1.7 on 2023-04-11 18:10

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0025_alter_comment_body'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='rating',
            field=models.DecimalField(decimal_places=1, default=1, max_digits=2, validators=[django.core.validators.MinValueValidator(Decimal('1')), django.core.validators.MaxValueValidator(Decimal('5'))]),
        ),
    ]