# Generated by Django 4.1.7 on 2023-10-21 12:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0014_alter_profile_photo_alter_profile_user'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profile',
            options={'ordering': ('user_id',)},
        ),
    ]
