# Generated by Django 4.1.7 on 2023-03-25 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0019_rename_value_property_text_value_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='text_value',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
