# Generated by Django 5.0.8 on 2025-01-17 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0013_alter_product_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='weight_unit',
            field=models.CharField(blank=True, choices=[('g', 'Gramos'), ('kg', 'Kilos'), ('l', 'Litros'), ('ml', 'Mililitros'), ('cm3', 'Centímetros cúbicos')], max_length=3, null=True),
        ),
    ]
