# Generated by Django 5.0.8 on 2024-10-02 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0015_return_total'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='needs_delivery',
            field=models.BooleanField(default=False),
        ),
    ]
