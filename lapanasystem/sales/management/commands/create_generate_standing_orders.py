"""Script to create a periodic task for create daily sales of one customer."""

# Django
from django.core.management.base import BaseCommand
from django.utils.timezone import now

# Celery
from django_celery_beat.models import PeriodicTask, CrontabSchedule


class Command(BaseCommand):
    help = 'Create a periodic task for create daily sales of one customer'

    def handle(self, *args, **kwargs):
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='0',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        if not PeriodicTask.objects.filter(name='Create standing orders at 00:00.').exists():
            PeriodicTask.objects.create(
                crontab=schedule,
                name='Create standing orders at 00:00.',
                task='create_daily_sales',
                start_time=now(),
            )
            self.stdout.write(self.style.SUCCESS('Periodic task created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Periodic task already exists'))
