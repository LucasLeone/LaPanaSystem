"""Script to create a periodic task for checking and updating subscriptions daily"""

# Django
from django.core.management.base import BaseCommand
from django.utils.timezone import now

# Celery
from django_celery_beat.models import PeriodicTask, CrontabSchedule


class Command(BaseCommand):
    help = 'Create a periodic task for checking and updating subscriptions daily'

    def handle(self, *args, **kwargs):
        # Crear o obtener el CrontabSchedule para las 3:00 AM
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='3',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        # Verificar si ya existe la tarea periódica
        if not PeriodicTask.objects.filter(name='Check and update sales at 3:00 AM').exists():
            # Crear la tarea periódica
            PeriodicTask.objects.create(
                crontab=schedule,
                name='Check and update sales at 3:00 AM',
                task='check_sales_for_delivery',
                start_time=now(),
            )
            self.stdout.write(self.style.SUCCESS('Periodic task created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Periodic task already exists'))
