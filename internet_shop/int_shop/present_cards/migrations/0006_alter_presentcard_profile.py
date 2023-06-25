# Generated by Django 4.1.7 on 2023-04-23 19:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0012_profile_phone_number'),
        ('present_cards', '0005_alter_presentcard_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presentcard',
            name='profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='profile_cards', to='account.profile'),
        ),
    ]