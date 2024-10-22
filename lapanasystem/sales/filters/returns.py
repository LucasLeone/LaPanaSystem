"""Return filters."""

# Django
import django_filters

# Models
from lapanasystem.sales.models import Return
from lapanasystem.customers.models import Customer
from lapanasystem.users.models import User

# Utilities
from django.utils import timezone
from django.db.models import Q


class ReturnFilter(django_filters.FilterSet):
    """Return filter."""

    min_total = django_filters.NumberFilter(field_name="total", lookup_expr='gte')
    max_total = django_filters.NumberFilter(field_name="total", lookup_expr='lte')
    start_date = django_filters.DateFilter(field_name="date", lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name="date", lookup_expr='lte')
    date = django_filters.DateFilter(field_name="date", method='filter_by_date')
    customer = django_filters.ModelChoiceFilter(
        queryset=Customer.objects.all(),
        field_name='sale__customer',
        label='Cliente'
    )
    user = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    search = django_filters.CharFilter(method='filter_by_search', label='Search')

    class Meta:
        model = Return
        fields = ['customer', 'min_total', 'max_total', 'start_date', 'end_date', 'user']

    def filter_by_date(self, queryset, name, value):
        """Filter by date ignoring time (full day)."""
        start_of_day = timezone.make_aware(timezone.datetime.combine(value, timezone.datetime.min.time()))
        end_of_day = timezone.make_aware(timezone.datetime.combine(value, timezone.datetime.max.time()))
        return queryset.filter(date__range=(start_of_day, end_of_day))

    def filter_by_search(self, queryset, name, value):
        """Filter returns by searching customer name or return ID."""
        return queryset.filter(
            Q(sale__customer__name__icontains=value) | Q(id__icontains=value)
        )
