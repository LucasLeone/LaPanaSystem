"""Customers admin."""

# Django
from django.contrib import admin

# Models
from lapanasystem.customers.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Customer admin."""

    list_display = ('id', 'name', 'email', 'phone_number', 'customer_type', 'created', 'modified', 'is_active')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'email', 'phone_number')
    list_filter = ('created', 'modified', 'is_active', 'customer_type')
    ordering = ('-created',)
    readonly_fields = ('created', 'modified')
