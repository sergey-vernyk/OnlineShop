# Generated by Django 4.1.7 on 2023-03-18 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0009_alter_propertycategory_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='units',
            field=models.CharField(blank=True, max_length=10),
        ),
    ]