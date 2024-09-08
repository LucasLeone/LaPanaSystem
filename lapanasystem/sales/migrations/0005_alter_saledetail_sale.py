# Generated by Django 5.0.8 on 2024-09-08 21:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0004_alter_sale_total'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saledetail',
            name='sale',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sale_details', to='sales.sale'),
        ),
    ]
