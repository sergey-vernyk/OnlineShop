# Generated by Django 4.1.7 on 2023-10-20 19:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0037_alter_property_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ('name',), 'verbose_name': 'Category', 'verbose_name_plural': 'Categories'},
        ),
        migrations.AlterModelOptions(
            name='favorite',
            options={'verbose_name': 'Favorite', 'verbose_name_plural': 'Favorites'},
        ),
    ]
