"""Celery tasks."""

# Django
from django.utils import timezone
from django.db import transaction

# Models
from lapanasystem.sales.models import Sale, StateChange, StandingOrder
from lapanasystem.products.models import Product
from lapanasystem.users.models import User
from lapanasystem.sales.models import SaleDetail

# Celery
from celery import shared_task

# Utilities
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


@shared_task(name='change_state_to_ready_for_delivery')
def change_state_to_ready_for_delivery(sale_id):
    """Change state to ready for delivery if the current state is 'CREADA'."""
    try:
        sale = Sale.objects.get(id=sale_id)
        logger.info(f"Processing sale with id {sale_id}.")
    except Sale.DoesNotExist:
        logger.error(f"Sale with id {sale_id} does not exist.")
        return {"status": "failed", "reason": "Sale does not exist."}

    with transaction.atomic():
        last_state_change = StateChange.objects.select_for_update().filter(sale=sale).order_by('-start_date').first()

        if last_state_change and last_state_change.state == StateChange.CREADA:
            if last_state_change.end_date is None:
                last_state_change.end_date = timezone.now()
                last_state_change.save()
                logger.info(f"Updated end_date for last_state_change id {last_state_change.id}.")

            # Crear nuevo estado
            new_state_change = StateChange.objects.create(sale=sale, state=StateChange.PENDIENTE_ENTREGA)
            logger.info(f"Created new state_change id {new_state_change.id} with state '{StateChange.PENDIENTE_ENTREGA}'.")
            return {"status": "success", "sale_id": sale_id, "new_state": StateChange.PENDIENTE_ENTREGA}
        else:
            logger.info(f"Sale with id {sale_id} is not in 'CREADA' state or already has an end_date.")
            return {"status": "no_action", "sale_id": sale_id}


@shared_task(name='create_daily_sales')
def create_daily_sales():
    """Crear ventas diarias basadas en pedidos recurrentes."""
    current_weekday = timezone.now().weekday()

    standing_orders = StandingOrder.objects.filter(day_of_week=current_weekday)

    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.first()

    for standing_order in standing_orders:
        customer = standing_order.customer

        with transaction.atomic():
            sale = Sale.objects.create(
                user=user,
                customer=customer,
                sale_type=Sale.MAYORISTA,
                needs_delivery=True,
                payment_method=Sale.EFECTIVO,
                date=timezone.now(),
            )

            total = Decimal('0.00')

            for detail in standing_order.details.all():
                product = detail.product
                quantity = detail.quantity

                if sale.sale_type == Sale.MAYORISTA:
                    price = product.wholesale_price or product.retail_price
                else:
                    price = product.retail_price

                if not price or price <= 0:
                    continue

                subtotal = price * quantity
                total += subtotal

                SaleDetail.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    price=price,
                )

            sale.total = total
            sale.save()

            StateChange.objects.create(sale=sale, state=StateChange.CREADA)

            if sale.needs_delivery:
                eta = sale.date
                change_state_to_ready_for_delivery.apply_async(args=[sale.id], eta=eta)
