# Generated by Django 5.0.8 on 2024-09-22 15:08

import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0011_sale_payment_method'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saledetail',
            name='quantity',
            field=models.DecimalField(decimal_places=3, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.001'))]),
        ),
    ]
