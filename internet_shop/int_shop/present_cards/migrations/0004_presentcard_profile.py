# Generated by Django 4.1.7 on 2023-03-08 13:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0010_remove_profile_present_card'),
        ('present_cards', '0003_alter_category_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='presentcard',
            name='profile',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='profile_cards', to='account.profile'),
            preserve_default=False,
        ),
    ]
