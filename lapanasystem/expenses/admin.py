"""Expenses admin."""

# Django
from django.contrib import admin

# Models
from lapanasystem.expenses.models import Expense, ExpenseCategory, Supplier


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """Expense admin."""

    list_display = ["id", "user", "amount", "date", "category", "supplier", "is_active"]
    list_display_links = ["id", "user"]
    search_fields = ["user__username", "category__name", "supplier__name"]
    list_filter = ["date", "category", "supplier"]
    list_editable = ["is_active",]


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    """ExpenseCategory admin."""

    list_display = ["id", "name", "description", "is_active"]
    list_display_links = ["id", "name"]
    search_fields = ["name"]
    list_editable = ["is_active",]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Supplier admin."""

    list_display = ["id", "name", "phone_number", "email", "address", "is_active"]
    list_display_links = ["id", "name"]
    search_fields = ["name", "phone_number", "email"]
    list_editable = ["is_active",]
