# Generated by Django 5.0.8 on 2024-09-06 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0003_remove_customer_phone_customer_phone_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='customer_type',
            field=models.CharField(choices=[('minorista', 'Minorista'), ('mayorista', 'Mayorista')], default='minorista', max_length=10, verbose_name='Tipo de cliente'),
        ),
        migrations.DeleteModel(
            name='CustomerType',
        ),
    ]
