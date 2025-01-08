"""Sales views."""

# Django
from decimal import Decimal
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Sum, OuterRef, Subquery, Count
from django.db.models.functions import TruncDate, Coalesce, TruncMonth
from django.db import transaction

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
from lapanasystem.sales.models import (
    Sale,
    StateChange,
    Return,
    SaleDetail,
    ReturnDetail,
)
from lapanasystem.expenses.models import Expense

# Serializers
from lapanasystem.sales.serializers import (
    SaleSerializer,
    PartialChargeSerializer,
    FastSaleSerializer,
)

# Filters
from lapanasystem.sales.filters import SaleFilter

# Utilities
from datetime import date, datetime, timedelta
from collections import defaultdict
from lapanasystem.utils.views import iso_year_week_to_range


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
    ordering_fields = [
        "id",
        "date",
        "total",
        "customer__name",
        "user__username",
        "total_collected",
    ]

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "cancel",
            "retrieve",
            "create_fast_sale",
            "update_fast_sale",
        ]:
            permissions = [IsAuthenticated, IsSeller | IsAdmin]
        elif self.action in [
            "mark_as_delivered",
            "mark_as_charged",
            "mark_as_partial_charged",
            "list_by_customer_for_collect",
        ]:
            permissions = [IsAuthenticated, IsDelivery | IsAdmin]
        elif self.action == "statistics":
            permissions = [IsAuthenticated, IsAdmin]
        elif self.action == "list":
            permissions = [IsAuthenticated]
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
    @transaction.atomic
    def mark_as_charged(self, request, *args, **kwargs):
        """Mark a sale as charged."""
        instance = self.get_object()

        last_state_change = instance.state_changes.order_by("-start_date").first()

        if not last_state_change:
            raise ValidationError("La venta no tiene un estado previo.")

        if last_state_change.state == StateChange.CANCELADA:
            raise ValidationError("La venta ya ha sido cancelada.")

        if last_state_change.state == StateChange.COBRADA:
            raise ValidationError("La venta ya ha sido marcada como cobrada.")

        total_returns = instance.returns.aggregate(total=Sum("total"))[
            "total"
        ] or Decimal("0.00")

        total_to_collect = instance.total - total_returns

        if total_to_collect < 0:
            raise ValidationError("El total a cobrar no puede ser negativo.")

        instance.total_collected = total_to_collect
        instance.save()

        last_state_change.end_date = timezone.now()
        last_state_change.save()

        StateChange.objects.create(sale=instance, state=StateChange.COBRADA)

        return Response(
            {"message": "Venta marcada como cobrada."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="mark-as-partial-charged")
    @transaction.atomic
    def mark_as_partial_charged(self, request, *args, **kwargs):
        """Mark a sale as partially charged."""
        instance = self.get_object()

        serializer = PartialChargeSerializer(
            data=request.data, context={"sale": instance}
        )
        serializer.is_valid(raise_exception=True)
        partial_total = serializer.validated_data["total"]

        if partial_total <= 0:
            raise ValidationError("El monto debe ser mayor que cero.")

        total_returns = instance.returns.aggregate(total=Sum("total"))[
            "total"
        ] or Decimal("0.00")

        total_to_collect = instance.total - total_returns

        if instance.total_collected + partial_total > total_to_collect:
            raise ValidationError(
                "El monto parcial no puede exceder el total a cobrar después de considerar devoluciones."
            )

        instance.total_collected += partial_total
        instance.save()

        last_state_change = instance.state_changes.order_by("-start_date").first()
        if last_state_change:
            last_state_change.end_date = timezone.now()
            last_state_change.save()

        if instance.total_collected == total_to_collect:
            new_state = StateChange.COBRADA
            message = "Venta marcada como cobrada."
        else:
            new_state = StateChange.COBRADA_PARCIAL
            message = "Venta marcada como cobrada parcialmente."

        StateChange.objects.create(sale=instance, state=new_state)

        return Response(
            {"message": message},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="create-fast-sale")
    def create_fast_sale(self, request, *args, **kwargs):
        """
        Creates a fast sale.

        Expects a JSON body with the following fields:
            - customer: Customer ID (Optional).
            - total: Total amount of the sale.
            - payment_method: Payment method (Optional, It's gonna be Efectivo if it's null).
            - date: Sale date (Optional, It's gonna be the current date if it's null).

        Returns:
            Response: A response indicating that the sale has been created.
        """
        serializer = FastSaleSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()

        sale_data = SaleSerializer(sale, context={"request": request}).data

        return Response(
            {"sale": sale_data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["put"], url_path="update-fast-sale")
    def update_fast_sale(self, request, *args, **kwargs):
        """
        Updates a fast sale.

        Expects a JSON body with the following fields:
            - customer: Customer ID (Optional).
            - total: Total amount of the sale.
            - payment_method: Payment method (Optional, It's gonna be Efectivo if it's null).
            - date: Sale date (Optional, It's gonna be the current date if it's null).

        Returns:
            Response: A response indicating that the sale has been updated.
        """
        instance = self.get_object()

        serializer = FastSaleSerializer(
            instance, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()

        sale_data = SaleSerializer(sale, context={"request": request}).data

        return Response(
            {"sale": sale_data},
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

        if last_state_change.state == StateChange.ANULADA:
            raise ValidationError("La venta ya ha sido anulada.")

        if (
            last_state_change.state == StateChange.CREADA
            or last_state_change.state == StateChange.PENDIENTE_ENTREGA
            or last_state_change.state == StateChange.ENTREGADA
        ):
            last_state_change.end_date = timezone.now()
            last_state_change.save()

            StateChange.objects.create(sale=instance, state=StateChange.CANCELADA)
            return Response(
                {"message": "Venta marcada como cancelada."},
                status=status.HTTP_200_OK,
            )

        if (
            last_state_change.state == StateChange.COBRADA
            or last_state_change.state == StateChange.COBRADA_PARCIAL
        ):
            last_state_change.end_date = timezone.now()
            last_state_change.save()

            StateChange.objects.create(sale=instance, state=StateChange.ANULADA)
            return Response(
                {"message": "Venta marcada como anulada."},
                status=status.HTTP_200_OK,
            )

    @action(detail=False, methods=["get"], url_path="list-by-customer-for-collect")
    def list_by_customer_for_collect(self, request, *args, **kwargs):
        """
        List sales by customer for collect.

        Show the total amount to collect for each customer.
        Must subtract the return from the sale and the amount already collected.
        Must filter sales with state "ENTREGADA" or "COBRADA_PARCIAL".

        Returns:
            Response: A response containing the sales by customer for collect.
        """
        latest_state_subquery = (
            StateChange.objects.filter(sale=OuterRef("pk"))
            .order_by("-start_date")
            .values("state")[:1]
        )

        sales_qs = (
            Sale.objects.filter(is_active=True, sale_type=Sale.MAYORISTA)
            .annotate(latest_state=Subquery(latest_state_subquery))
            .filter(
                latest_state__in=[StateChange.ENTREGADA, StateChange.COBRADA_PARCIAL]
            )
            .annotate(total_returns=Coalesce(Sum("returns__total"), Decimal("0.00")))
            .select_related("customer")
        )

        customers = defaultdict(
            lambda: {
                "name": "",
                "total_sales": Decimal("0.00"),
                "total_discounted": Decimal("0.00"),
                "total_collected": Decimal("0.00"),
                "total_to_collect": Decimal("0.00"),
                "sales_to_collect": [],
            }
        )

        for sale in sales_qs:
            customer = sale.customer
            if not customer:
                continue

            customer_id = customer.id
            customers[customer_id]["name"] = customer.name
            customers[customer_id]["total_sales"] += sale.total
            customers[customer_id]["total_discounted"] += sale.total_returns
            customers[customer_id]["total_collected"] += sale.total_collected

            total_to_collect_sale = (
                sale.total - sale.total_returns - sale.total_collected
            )

            customers[customer_id]["sales_to_collect"].append(
                {
                    "id": sale.id,
                    "date": sale.date.isoformat(),
                    "total": f"{sale.total:.2f}",
                    "total_returns": f"{sale.total_returns:.2f}",
                    "total_collected": f"{sale.total_collected:.2f}",
                    "total_to_collect": f"{total_to_collect_sale:.2f}",
                    "sale_details": SaleSerializer(sale).data,
                }
            )

        response_data = []
        for customer_data in customers.values():
            total_sales = customer_data["total_sales"]
            total_discounted = customer_data["total_discounted"]
            total_collected = customer_data["total_collected"]
            total_to_collect = total_sales - total_discounted - total_collected

            response_data.append(
                {
                    "name": customer_data["name"],
                    "total_sales": f"{total_sales:.2f}",
                    "total_discounted": f"{total_discounted:.2f}",
                    "total_collected": f"{total_collected:.2f}",
                    "total_to_collect": f"{total_to_collect:.2f}",
                    "sales_to_collect": customer_data["sales_to_collect"],
                }
            )

        return Response(
            {"customers": response_data},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request, *args, **kwargs):
        """Statistics for sales."""
        latest_state_subquery = (
            StateChange.objects.filter(sale=OuterRef("pk"))
            .order_by("-start_date")
            .values("state")[:1]
        )

        sales_qs = (
            Sale.objects.filter(is_active=True)
            .annotate(latest_state=Subquery(latest_state_subquery))
            .filter(latest_state=StateChange.COBRADA)
        )
        returns_qs = Return.objects.all()
        expenses_qs = Expense.objects.all()

        data = {
            "total_sales_count": 0,
            "total_sales": "0.00",
            "total_collected_amount": "0.00",
            "total_returns_amount": "0.00",
            "total_expenses": "0.00",
            "total_profit": "0.00",
            "most_sold_products": [],
        }

        param_today = "today" in request.query_params
        param_month = request.query_params.get("month")
        param_week = request.query_params.get("week")
        param_year = request.query_params.get("year")
        param_start_date = request.query_params.get("start_date")
        param_end_date = request.query_params.get("end_date")

        params_count = sum(
            [
                1
                for x in [
                    param_today,
                    param_month,
                    param_week,
                    param_year,
                    (param_start_date and param_end_date),
                ]
                if x
            ]
        )
        if params_count == 0:
            raise ValidationError(
                "Debes proporcionar un parámetro de rango de fechas (today, month=YYYY-MM, "
                "week=YYYY-WW, year=YYYY o start_date/end_date)."
            )
        if params_count > 1:
            raise ValidationError(
                "Solo se permite un parámetro de rango de fechas a la vez."
            )

        start_date = end_date = None

        if param_today:
            today = datetime.now().date()
            start_date = end_date = today
        elif param_week:
            try:
                year_str, week_num_str = param_week.split("-W")
                iso_year = int(year_str)
                iso_week = int(week_num_str)
                start_date, end_date = iso_year_week_to_range(iso_year, iso_week)
            except ValueError:
                raise ValidationError("Formato de semana inválido. Usa YYYY-WW.")
        elif param_month:
            try:
                year, month_num = map(int, param_month.split("-"))
                start_date = date(year, month_num, 1)
                end_date = (
                    date(year, 12, 31)
                    if month_num == 12
                    else (date(year, month_num + 1, 1) - timedelta(days=1))
                )
            except ValueError:
                raise ValidationError("Formato de mes inválido. Usa YYYY-MM.")
        elif param_year:
            try:
                year = int(param_year)
                start_date = date(year, 1, 1)
                end_date = date(year, 12, 31)
            except ValueError:
                raise ValidationError("Formato de año inválido. Usa YYYY.")
        elif param_start_date and param_end_date:
            from django.utils.dateparse import parse_date

            try:
                sd = parse_date(param_start_date)
                ed = parse_date(param_end_date)
                if not sd or not ed or sd > ed:
                    raise ValueError
                start_date, end_date = sd, ed
            except ValueError:
                raise ValidationError(
                    "Formato de fecha inválido o fecha de inicio posterior a fecha fin. Usa YYYY-MM-DD."
                )

        start_dt = timezone.make_aware(
            datetime.combine(start_date, datetime.min.time()),
            timezone.get_current_timezone(),
        )
        end_dt = timezone.make_aware(
            datetime.combine(end_date, datetime.max.time()),
            timezone.get_current_timezone(),
        )

        sales_filtered = sales_qs.filter(date__range=(start_dt, end_dt))
        returns_filtered = returns_qs.filter(date__range=(start_dt, end_dt))
        expenses_filtered = expenses_qs.filter(date__range=(start_dt, end_dt))

        total_sales_amount = sales_filtered.aggregate(total_sales=Sum("total"))[
            "total_sales"
        ] or Decimal("0.00")
        total_collected_amount = sales_filtered.aggregate(
            total_collected=Sum("total_collected")
        )["total_collected"] or Decimal("0.00")
        total_returns_amount = returns_filtered.aggregate(total=Sum("total"))[
            "total"
        ] or Decimal("0.00")
        total_expenses = expenses_filtered.aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")
        total_profit = total_collected_amount - total_returns_amount - total_expenses
        total_sales_count = sales_filtered.count()

        data.update(
            {
                "total_sales_count": total_sales_count,
                "total_sales": str(total_sales_amount),
                "total_collected_amount": str(total_collected_amount),
                "total_returns_amount": str(total_returns_amount),
                "total_expenses": str(total_expenses),
                "total_profit": str(total_profit.quantize(Decimal("0.01"))),
            }
        )

        sale_details_qs = SaleDetail.objects.filter(sale__in=sales_filtered)
        sold_aggregated = sale_details_qs.values(
            "product__name", "product__slug"
        ).annotate(total_sold=Sum("quantity"))

        returned_details_qs = ReturnDetail.objects.filter(
            return_order__in=returns_filtered,
            return_order__sale__in=sales_filtered,
        )
        returned_aggregated = returned_details_qs.values(
            "product__name", "product__slug"
        ).annotate(total_returned=Sum("quantity"))

        sold_dict = {
            item["product__slug"]: {
                "product_name": item["product__name"],
                "total_sold": item["total_sold"] or Decimal("0"),
            }
            for item in sold_aggregated
        }

        returned_dict = {
            item["product__slug"]: item["total_returned"] or Decimal("0")
            for item in returned_aggregated
        }

        results = []
        for slug, sold_data in sold_dict.items():
            total_sold = sold_data["total_sold"]
            total_returned = returned_dict.get(slug, Decimal("0"))
            net_sold = total_sold - total_returned

            results.append(
                {
                    "product_name": sold_data["product_name"],
                    "product_slug": slug,
                    "total_quantity_sold": net_sold,
                }
            )

        results.sort(key=lambda x: x["total_quantity_sold"], reverse=True)
        data["most_sold_products"] = results[:5]

        if param_year:
            sales_monthly = (
                sales_filtered.annotate(month_only=TruncMonth("date"))
                .values("month_only")
                .annotate(
                    sales_count=Count("id"),
                    total_sales=Sum("total"),
                    total_collected=Sum("total_collected"),
                )
                .order_by("month_only")
            )
            returns_monthly = (
                returns_filtered.annotate(month_only=TruncMonth("date"))
                .values("month_only")
                .annotate(total_returns=Sum("total"))
                .order_by("month_only")
            )
            expenses_monthly = (
                expenses_filtered.annotate(month_only=TruncMonth("date"))
                .values("month_only")
                .annotate(total_expenses=Sum("amount"))
                .order_by("month_only")
            )

            sales_dict = {item["month_only"].date(): item for item in sales_monthly}
            returns_dict = {item["month_only"].date(): item for item in returns_monthly}
            expenses_dict = {
                item["month_only"].date(): item for item in expenses_monthly
            }

            breakdown = []
            current_month = date(start_date.year, start_date.month, 1)
            last_month = date(end_date.year, end_date.month, 1)

            while current_month <= last_month:
                s_data = sales_dict.get(current_month, {})
                r_data = returns_dict.get(current_month, {})
                e_data = expenses_dict.get(current_month, {})

                sales_count_ = s_data.get("sales_count", 0)
                total_sales_ = s_data.get("total_sales", Decimal("0.00"))
                total_collected_ = s_data.get("total_collected", Decimal("0.00"))
                total_returns_ = r_data.get("total_returns", Decimal("0.00"))
                monthly_expenses_ = e_data.get("total_expenses", Decimal("0.00"))
                monthly_profit_ = total_collected_ - monthly_expenses_

                if any(
                    [
                        sales_count_,
                        total_sales_,
                        total_collected_,
                        total_returns_,
                        monthly_expenses_,
                        monthly_profit_,
                    ]
                ):
                    breakdown.append(
                        {
                            "month": current_month.strftime("%Y-%m"),
                            "sales_count": sales_count_,
                            "total_sales": str(total_sales_),
                            "total_collected": str(total_collected_),
                            "total_returns": str(total_returns_),
                            "monthly_expenses": str(monthly_expenses_),
                            "monthly_profit": str(monthly_profit_),
                        }
                    )

                if current_month.month == 12:
                    year_, month_ = current_month.year + 1, 1
                else:
                    year_, month_ = current_month.year, current_month.month + 1
                current_month = date(year_, month_, 1)

            data["monthly_breakdown"] = breakdown

        else:
            sales_daily = (
                sales_filtered.annotate(date_only=TruncDate("date"))
                .values("date_only")
                .annotate(
                    sales_count=Count("id"),
                    total_sales=Sum("total"),
                    total_collected=Sum("total_collected"),
                )
                .order_by("date_only")
            )
            returns_daily = (
                returns_filtered.annotate(date_only=TruncDate("date"))
                .values("date_only")
                .annotate(total_returns=Sum("total"))
                .order_by("date_only")
            )
            expenses_daily = (
                expenses_filtered.annotate(date_only=TruncDate("date"))
                .values("date_only")
                .annotate(total_expenses=Sum("amount"))
                .order_by("date_only")
            )

            sales_dict = {item["date_only"]: item for item in sales_daily}
            returns_dict = {item["date_only"]: item for item in returns_daily}
            expenses_dict = {item["date_only"]: item for item in expenses_daily}

            breakdown = []
            current_day = start_date
            while current_day <= end_date:
                s_data = sales_dict.get(current_day, {})
                r_data = returns_dict.get(current_day, {})
                e_data = expenses_dict.get(current_day, {})

                sales_count_ = s_data.get("sales_count", 0)
                total_sales_ = s_data.get("total_sales", Decimal("0.00"))
                total_collected_ = s_data.get("total_collected", Decimal("0.00"))
                total_returns_ = r_data.get("total_returns", Decimal("0.00"))
                daily_expenses_ = e_data.get("total_expenses", Decimal("0.00"))
                daily_profit_ = total_collected_ - daily_expenses_

                if any(
                    [
                        sales_count_,
                        total_sales_,
                        total_collected_,
                        total_returns_,
                        daily_expenses_,
                        daily_profit_,
                    ]
                ):
                    breakdown.append(
                        {
                            "date": current_day.isoformat(),
                            "sales_count": sales_count_,
                            "total_sales": str(total_sales_),
                            "total_collected": str(total_collected_),
                            "total_returns": str(total_returns_),
                            "daily_expenses": str(daily_expenses_),
                            "daily_profit": str(daily_profit_),
                        }
                    )

                current_day += timedelta(days=1)

            data["daily_breakdown"] = breakdown

        return Response(data, status=status.HTTP_200_OK)
