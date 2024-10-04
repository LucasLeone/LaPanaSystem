"""Celery tasks."""

# Django
from django.db.models import OuterRef, Subquery
from django.utils import timezone

# Models
from lapanasystem.sales.models import Sale, StateChange

# Celery
from celery import shared_task

# Utilities
from datetime import date


@shared_task(name='change_state_to_ready_for_delivery')
def change_state_to_ready_for_delivery(sale_id):
    """Change state to ready for delivery if the current state is 'creada'."""
    sale = Sale.objects.get(id=sale_id)

    last_state_change = StateChange.objects.filter(sale=sale).order_by('-start_date').first()

    if last_state_change and last_state_change.state == StateChange.CREADA:
        if last_state_change.end_date is None:
            last_state_change.end_date = timezone.now()
            last_state_change.save()

        StateChange.objects.create(sale=sale, state=StateChange.PENDIENTE_ENTREGA)
