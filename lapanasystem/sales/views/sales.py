"""Sales views."""

# Django
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, OuterRef, Subquery, Count
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404

# Django REST Framework
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

# Permissions
from rest_framework.permissions import IsAuthenticated
from lapanasystem.users.permissions import IsAdmin, IsSeller, IsDelivery

# Models
from lapanasystem.sales.models import Sale, StateChange, Return, SaleDetail
from lapanasystem.expenses.models import Expense
from lapanasystem.products.models import Product

# Serializers
from lapanasystem.sales.serializers import SaleSerializer

# Filters
from lapanasystem.sales.filters import SaleFilter

# Utilities
from datetime import datetime, timedelta


class SaleViewSet(ModelViewSet):
    """
    Sale view set.

    Handle the creation, updating, and deletion of sales.

    Actions:
        - List: Return a list of sales.
        - Retrieve: Return a sale.
        - Create: Create a sale with or without details.
        - Update: Update a sale.
        - Partial update: Update a sale partially.
        - Destroy: Delete a sale.
        - Cancel: Cancel a sale.
        - Mark as delivered: Mark a sale as delivered.
        - Mark as charged: Mark a sale as charged.
        - Statistics: Get sales statistics.

    Filters:
        - Search: Search sales by customer name or seller username.
        - Ordering: Order sales by date or total.
        - Filter: Filter sales by state, customer, or user.

    Permissions:
        - List: IsAuthenticated, IsSeller | IsAdmin
        - Retrieve: IsAuthenticated, IsSeller | IsAdmin
        - Create: IsAuthenticated, IsSeller | IsAdmin
        - Update: IsAuthenticated, IsSeller | IsAdmin
        - Partial update: IsAuthenticated, IsSeller | IsAdmin
        - Destroy: IsAuthenticated, IsSeller | IsAdmin
        - Cancel: IsAuthenticated, IsSeller | IsAdmin
        - Mark as delivered: IsAuthenticated, IsDelivery | IsAdmin
        - Mark as charged: IsAuthenticated, IsDelivery | IsAdmin
        - Statistics: IsAuthenticated, IsAdmin
    """

    queryset = Sale.objects.filter(is_active=True)
    serializer_class = SaleSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ["customer__name", "user__username"]
    filterset_class = SaleFilter
    ordering_fields = ["date", "total"]

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "cancel",
            "list",
            "retrieve",
        ]:
            permissions = [IsAuthenticated, IsSeller | IsAdmin]
        elif self.action in ["mark_as_delivered", "mark_as_charged"]:
            permissions = [IsAuthenticated, IsDelivery | IsAdmin]
        elif self.action == "statistics":
            permissions = [IsAuthenticated, IsAdmin]
        else:
            permissions = [IsAuthenticated, IsAdmin]
        return [p() for p in permissions]

    def perform_destroy(self, instance):
        """Disable delete (soft delete)."""
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        """Handle soft delete with confirmation message."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Sale deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=True, methods=["post"], url_path="mark-as-delivered")
    def mark_as_delivered(self, request, *args, **kwargs):
        """
        Marks a sale as delivered.

        Raises:
            ValidationError: If the sale has no previous state, if the sale has already been canceled,
                if the sale has already been marked as delivered, or if the sale has already been
                marked as paid.

        Returns:
            Response: A response indicating that the sale has been marked as delivered.
        """
        instance = self.get_object()

        last_state_change = instance.state_changes.order_by("-start_date").first()

        if not last_state_change:
            raise ValidationError("La venta no tiene un estado previo.")

        if last_state_change.state == StateChange.CANCELADA:
            raise ValidationError("La venta ya ha sido cancelada.")

        if last_state_change.state == StateChange.ENTREGADA:
            raise ValidationError("La venta ya ha sido marcada como entregada.")

        if last_state_change.state == StateChange.COBRADA:
            raise ValidationError("La venta ya ha sido cobrada.")

        last_state_change.end_date = timezone.now()
        last_state_change.save()

        StateChange.objects.create(sale=instance, state=StateChange.ENTREGADA)

        return Response(
            {"message": "Venta marcada como entregada."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="mark-as-charged")
    def mark_as_charged(self, request, *args, **kwargs):
        """
        Marks a sale as charged.

        Raises:
            ValidationError: If the sale has no previous state, if the sale has already been canceled,
                or if the sale has already been marked as charged.

        Returns:
            Response: A response indicating that the sale has been marked as charged.
        """
        instance = self.get_object()

        last_state_change = instance.state_changes.order_by("-start_date").first()

        if not last_state_change:
            raise ValidationError("La venta no tiene un estado previo.")

        if last_state_change.state == StateChange.CANCELADA:
            raise ValidationError("La venta ya ha sido cancelada.")

        if last_state_change.state == StateChange.COBRADA:
            raise ValidationError("La venta ya ha sido marcada como cobrada.")

        last_state_change.end_date = timezone.now()
        last_state_change.save()

        StateChange.objects.create(sale=instance, state=StateChange.COBRADA)

        return Response(
            {"message": "Venta marcada como cobrada."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, *args, **kwargs):
        """
        Cancels a sale.

        Raises:
            ValidationError: If the sale has no previous state, if the sale has already been canceled,
                or if the sale has already been marked as charged.

        Returns:
            Response: A response indicating that the sale has been canceled.
        """
        instance = self.get_object()

        last_state_change = instance.state_changes.order_by("-start_date").first()

        if not last_state_change:
            raise ValidationError("La venta no tiene un estado previo.")

        if last_state_change.state == StateChange.CANCELADA:
            raise ValidationError("La venta ya ha sido cancelada.")

        if last_state_change.state == StateChange.COBRADA:
            raise ValidationError("No se puede cancelar una venta ya cobrada.")

        last_state_change.end_date = timezone.now()
        last_state_change.save()

        StateChange.objects.create(sale=instance, state=StateChange.CANCELADA)

        return Response(
            {"message": "Venta marcada como cancelada."},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path='statistics')
    def statistics(self, request, *args, **kwargs):
        """
        Returns the sales statistics.

        Query Parameters:
            - start_date: Start date for custom range (YYYY-MM-DD).
            - end_date: End date for custom range (YYYY-MM-DD).
            - product_slug: (Optional) Slug of the product to filter sales.

        Returns:
            Response: A response containing the sales statistics.
        """
        # Helper function to get date ranges
        def get_date_ranges():
            today = timezone.now().date()
            current_timezone = timezone.get_current_timezone()

            # Inicio y fin del día de hoy
            start_of_today = timezone.make_aware(datetime.combine(today, datetime.min.time()), current_timezone)
            end_of_today = timezone.make_aware(datetime.combine(today, datetime.max.time()), current_timezone)

            # Inicio y fin de la semana (lunes a domingo)
            start_of_week = timezone.make_aware(datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time()), current_timezone)
            end_of_week = timezone.make_aware(datetime.combine(start_of_week.date() + timedelta(days=6), datetime.max.time()), current_timezone)

            # Inicio y fin del mes
            start_of_month = timezone.make_aware(datetime.combine(today.replace(day=1), datetime.min.time()), current_timezone)
            if today.month == 12:
                last_day_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last_day_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            end_of_month = timezone.make_aware(datetime.combine(last_day_of_month, datetime.max.time()), current_timezone)

            return {
                "today": {"start": start_of_today, "end": end_of_today},
                "week": {"start": start_of_week, "end": end_of_week},
                "month": {"start": start_of_month, "end": end_of_month},
            }

        date_ranges = get_date_ranges()

        # Parse custom date range si se proporciona
        custom_start = request.query_params.get('start_date')
        custom_end = request.query_params.get('end_date')

        if custom_start and custom_end:
            try:
                # Parse fechas sin zona horaria
                custom_start_date = datetime.strptime(custom_start, "%Y-%m-%d").date()
                custom_end_date = datetime.strptime(custom_end, "%Y-%m-%d").date()
                if custom_start_date > custom_end_date:
                    raise ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")
                # Asigna zona horaria
                custom_start_dt = timezone.make_aware(datetime.combine(custom_start_date, datetime.min.time()), timezone.get_current_timezone())
                custom_end_dt = timezone.make_aware(datetime.combine(custom_end_date, datetime.max.time()), timezone.get_current_timezone())
                date_ranges["custom"] = {"start": custom_start_dt, "end": custom_end_dt}
            except ValueError:
                raise ValidationError("Formato de fecha inválido. Use YYYY-MM-DD.")

        # Obtener product_slug si se proporciona
        product_slug = request.query_params.get('product_slug')
        product = None
        if product_slug:
            product = get_object_or_404(Product, slug=product_slug)

        # Subquery para obtener el último estado de cada venta
        latest_state_subquery = StateChange.objects.filter(
            sale=OuterRef('pk')
        ).order_by('-start_date').values('state')[:1]

        statistics = {}

        for period_name, range_dates in date_ranges.items():
            start = range_dates["start"]
            end = range_dates["end"]

            # Filtrar ventas activas dentro del rango y con estado 'COBRADA'
            sales_qs = Sale.objects.filter(
                date__gte=start,
                date__lte=end,
                is_active=True
            ).annotate(
                latest_state=Subquery(latest_state_subquery)
            ).filter(
                latest_state=StateChange.COBRADA
            )

            total_sales_count = sales_qs.count()
            total_sales_amount = sales_qs.aggregate(total=Sum('total'))['total'] or Decimal('0.00')

            # Filtrar devoluciones dentro del rango
            returns_qs = Return.objects.filter(date__gte=start, date__lte=end)
            total_returns_amount = returns_qs.aggregate(total=Sum('total'))['total'] or Decimal('0.00')

            # Ingresos netos
            net_revenue = (total_sales_amount - total_returns_amount).quantize(Decimal('0.01'))

            # Filtrar gastos dentro del rango
            expenses_qs = Expense.objects.filter(date__gte=start, date__lte=end)
            total_expenses = expenses_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            # Detalles de ventas para productos más vendidos
            sale_details_qs = SaleDetail.objects.filter(
                sale__in=sales_qs,
            )
            if product:
                sale_details_qs = sale_details_qs.filter(product=product)

            if product:
                total_product_sold = sale_details_qs.aggregate(
                    total_quantity=Sum('quantity')
                )['total_quantity'] or Decimal('0.00')
            else:
                most_sold_products = sale_details_qs.values(
                    'product__name',
                    'product__slug'
                ).annotate(
                    total_quantity=Sum('quantity')
                ).order_by('-total_quantity')[:5]
                most_sold_products = [
                    {
                        "product_name": item['product__name'],
                        "product_slug": item['product__slug'],
                        "total_quantity_sold": item['total_quantity']
                    }
                    for item in most_sold_products
                ]

            period_stats = {
                "total_sales_count": total_sales_count,
                "total_sales_amount": str(total_sales_amount),
                "total_returns_amount": str(total_returns_amount),
                "net_revenue": str(net_revenue),
                "total_expenses": str(total_expenses),
            }

            # Solo agregar 'daily_breakdown' si el periodo no es 'custom'
            if period_name != "custom":
                # ====== Agregar Desglose Diario ======
                # Agrupar ventas por fecha
                sales_daily = sales_qs.annotate(
                    date_only=TruncDate('date')
                ).values('date_only').annotate(
                    sales_count=Count('id'),
                    total_sales=Sum('total')
                ).order_by('date_only')

                # Agrupar devoluciones por fecha
                returns_daily = returns_qs.annotate(
                    date_only=TruncDate('date')
                ).values('date_only').annotate(
                    total_returns=Sum('total')
                ).order_by('date_only')

                # Convertir a diccionarios para fácil acceso
                sales_daily_dict = {item['date_only']: item for item in sales_daily}
                returns_daily_dict = {item['date_only']: item for item in returns_daily}

                # Generar una lista de fechas en el rango
                current_date = start.date()
                end_date = end.date()
                daily_breakdown = []
                while current_date <= end_date:
                    sales_data = sales_daily_dict.get(current_date, {})
                    returns_data = returns_daily_dict.get(current_date, {})
                    sales_count = sales_data.get('sales_count', 0)
                    total_sales = sales_data.get('total_sales', Decimal('0.00'))
                    total_returns = returns_data.get('total_returns', Decimal('0.00'))
                    net_collected = (total_sales - total_returns).quantize(Decimal('0.01'))

                    daily_breakdown.append({
                        "date": current_date.isoformat(),
                        "sales_count": sales_count,
                        "total_collected": str(total_sales),
                        "total_returns": str(total_returns),
                        "net_collected": str(net_collected),
                    })

                    current_date += timedelta(days=1)

                # Agregar el desglose diario al periodo
                period_stats["daily_breakdown"] = daily_breakdown

            if product:
                period_stats["product_slug"] = product_slug
                period_stats["product_name"] = product.name
                period_stats["total_quantity_sold"] = str(total_product_sold)
            else:
                period_stats["most_sold_products"] = most_sold_products

            statistics[period_name] = period_stats

        return Response(
            {"statistics": statistics},
            status=status.HTTP_200_OK,
        )
