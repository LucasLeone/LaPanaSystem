# Generated by Django 5.0.8 on 2024-09-13 21:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_alter_productcategory_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productbrand',
            options={'verbose_name': 'Product Brand', 'verbose_name_plural': 'Product Brands'},
        ),
        migrations.AlterModelOptions(
            name='productcategory',
            options={'verbose_name': 'Product Category', 'verbose_name_plural': 'Product Categories'},
        ),
    ]