# Generated by Django 4.1.7 on 2023-05-22 16:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('present_cards', '0006_alter_presentcard_profile'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='presentcard',
            options={},
        ),
        migrations.RemoveField(
            model_name='presentcard',
            name='active',
        ),
    ]