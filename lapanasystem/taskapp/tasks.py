"""Celery tasks."""

# Django
from django.db.models import OuterRef, Subquery

# Models
from lapanasystem.sales.models import Sale, StateChange

# Celery
from celery import shared_task

# Utilities
from datetime import date, datetime


@shared_task(name='change_state_to_ready_for_delivery')
def change_state_to_ready_for_delivery(sale_id):
    """Change state to ready for delivery."""
    sale = Sale.objects.get(id=sale_id)

    last_state_change = StateChange.objects.filter(sale=sale).order_by('-start_date').first()

    if last_state_change and last_state_change.end_date is None:
        last_state_change.end_date = datetime.now()
        last_state_change.save()

    StateChange.objects.create(sale=sale, state=StateChange.PENDIENTE_ENTREGA)

    return sale


@shared_task(name='check_sales_for_delivery')
def check_sales_for_delivery():
    """Check all sales with today's date and change their state to 'Pending for delivery'."""
    today = date.today()

    last_state_change = StateChange.objects.filter(
        sale=OuterRef('pk')
    ).order_by('-start_date')

    sales = Sale.objects.filter(
        date__date=today,
        is_active=True,
        state_changes__state=Subquery(last_state_change.values('state')[:1])
    )

    for sale in sales:
        change_state_to_ready_for_delivery.delay(sale.id)
