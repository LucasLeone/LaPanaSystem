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


@shared_task(name='check_sales_for_delivery')
def check_sales_for_delivery():
    """Check all sales with today's date and change their state to 'Pending for delivery'."""
    today = date.today()

    last_state_subquery = StateChange.objects.filter(
        sale=OuterRef('pk')
    ).order_by('-start_date').values('state')[:1]

    sales = Sale.objects.filter(
        date__date=today,
        is_active=True
    ).annotate(
        last_state=Subquery(last_state_subquery)
    ).filter(
        last_state=StateChange.CREADA
    )

    for sale in sales:
        change_state_to_ready_for_delivery.delay(sale.id)
