# Generated by Django 5.0.8 on 2024-09-18 20:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_alter_product_wholesale_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='weight_unit',
            field=models.CharField(blank=True, choices=[('g', 'Gramos'), ('kg', 'Kilos')], max_length=2, null=True),
        ),
    ]
