# Generated by Django 4.1.7 on 2023-02-26 12:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
        ('goods', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='profile',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='profile_comments', to='account.profile'),
        ),
    ]
