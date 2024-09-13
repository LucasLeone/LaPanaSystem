"""Sales admin."""

# Django
from django.contrib import admin

# Models
from lapanasystem.sales.models import Sale, SaleDetail, StateChange


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    """Sale admin."""

    list_display = ('id', 'customer', 'total', 'sale_type', 'date', 'get_state', 'is_active')
    list_display_links = ('id', 'customer')
    search_fields = ('customer__name', 'customer__email')
    list_filter = ('sale_type', 'date')


@admin.register(SaleDetail)
class SaleDetailAdmin(admin.ModelAdmin):
    """Sale detail admin."""

    list_display = ('id', 'sale', 'product', 'quantity', 'price')
    list_display_links = ('id', 'sale')
    search_fields = ('sale__customer__name', 'product__name')


@admin.register(StateChange)
class StateChangeAdmin(admin.ModelAdmin):
    """State change admin."""

    list_display = ('id', 'sale', 'state', 'start_date', 'end_date')
    list_display_links = ('id', 'sale')
    search_fields = ('sale__customer__name', 'state')
    list_filter = ('state', 'start_date', 'end_date')