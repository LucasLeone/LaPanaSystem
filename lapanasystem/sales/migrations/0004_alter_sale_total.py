# Generated by Django 5.0.8 on 2024-09-06 22:40

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0003_alter_sale_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sale',
            name='total',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
