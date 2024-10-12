# Generated by Django 5.0.8 on 2024-10-12 13:54

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0006_alter_customer_address_alter_customer_phone_number'),
        ('sales', '0017_alter_sale_customer'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Collect',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='Date time on which the object was created.', verbose_name='created at')),
                ('modified', models.DateTimeField(auto_now=True, help_text='Date time on which the object was last modified.', verbose_name='modified at')),
                ('is_active', models.BooleanField(default=True, help_text='Set to False if you want to deactivate this record.', verbose_name='active')),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('total', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='customers.customer')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created', '-modified', '-is_active'],
                'get_latest_by': 'created',
                'abstract': False,
            },
        ),
    ]
