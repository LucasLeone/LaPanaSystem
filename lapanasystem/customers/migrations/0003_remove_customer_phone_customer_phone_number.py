# Generated by Django 5.0.8 on 2024-09-06 12:18

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0002_alter_customer_address_alter_customer_phone'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='phone',
        ),
        migrations.AddField(
            model_name='customer',
            name='phone_number',
            field=models.CharField(blank=True, max_length=17, validators=[django.core.validators.RegexValidator(message='Phone number must be entered in the format: +999999999. Up to 15 digits allowed.', regex='\\+?1?\\d{9,15}$')]),
        ),
    ]