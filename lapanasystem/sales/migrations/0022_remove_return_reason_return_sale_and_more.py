# Generated by Django 5.0.8 on 2024-10-16 22:23

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0021_remove_return_applied_amount'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='return',
            name='reason',
        ),
        migrations.AddField(
            model_name='return',
            name='sale',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.RESTRICT, to='sales.sale'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sale',
            name='total_collected',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))]),
        ),
    ]
