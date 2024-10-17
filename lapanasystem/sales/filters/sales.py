"""Sales filters."""

# Django
import django_filters
from django.db.models import OuterRef, Subquery

# Models
from lapanasystem.sales.models import Sale, StateChange
from lapanasystem.customers.models import Customer
from lapanasystem.users.models import User

# Utilities
from django.utils import timezone


class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    pass


class SaleFilter(django_filters.FilterSet):
    """Sale filter."""

    min_total = django_filters.NumberFilter(field_name="total", lookup_expr='gte')
    max_total = django_filters.NumberFilter(field_name="total", lookup_expr='lte')
    start_date = django_filters.DateFilter(field_name="date", lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name="date", lookup_expr='lte')
    date = django_filters.DateFilter(field_name="date", method='filter_by_date')
    state = CharInFilter(method='filter_by_state')
    needs_delivery = django_filters.BooleanFilter()
    customer = django_filters.ModelChoiceFilter(queryset=Customer.objects.all())
    user = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    payment_method = django_filters.CharFilter(method='filter_by_payment_method')

    class Meta:
        model = Sale
        fields = ['sale_type', 'customer', 'user']

    def filter_by_date(self, queryset, name, value):
        """Filter by date ignoring time (full day)."""
        start_of_day = timezone.make_aware(timezone.datetime.combine(value, timezone.datetime.min.time()))
        end_of_day = timezone.make_aware(timezone.datetime.combine(value, timezone.datetime.max.time()))
        return queryset.filter(date__range=(start_of_day, end_of_day))

    def filter_by_state(self, queryset, name, value):
        """Filter sales by their current state."""
        # value ahora es una lista de estados
        last_state_change = StateChange.objects.filter(
            sale=OuterRef('pk')
        ).order_by('-start_date')

        return queryset.annotate(
            current_state=Subquery(last_state_change.values('state')[:1])
        ).filter(current_state__in=value)

    def filter_by_payment_method(self, queryset, name, value):
        """Filter sales by payment method."""
        return queryset.filter(payment_method=value)
