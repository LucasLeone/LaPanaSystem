"""Collects filters."""

# Django
import django_filters
from django.utils import timezone

# Models
from lapanasystem.sales.models import Collect
from lapanasystem.customers.models import Customer
from lapanasystem.users.models import User


class CollectFilter(django_filters.FilterSet):
    """Collect filter."""

    start_date = django_filters.DateFilter(field_name="date", lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name="date", lookup_expr='lte')
    date = django_filters.DateFilter(field_name="date", method='filter_by_date')
    customer = django_filters.ModelChoiceFilter(queryset=Customer.objects.all())
    user = django_filters.ModelChoiceFilter(queryset=User.objects.all())

    class Meta:
        model = Collect
        fields = ['date', 'total']

    def filter_by_date(self, queryset, name, value):
        """Filter by date ignoring time (full day)."""
        start_of_day = timezone.make_aware(timezone.datetime.combine(value, timezone.datetime.min.time()))
        end_of_day = timezone.make_aware(timezone.datetime.combine(value, timezone.datetime.max.time()))
        return queryset.filter(date__range=(start_of_day, end_of_day))
