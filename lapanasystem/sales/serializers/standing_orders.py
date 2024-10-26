"""Standing orders serializers."""

# Django REST Framework
from rest_framework import serializers

# Models
from lapanasystem.sales.models import StandingOrder, StandingOrderDetail


class StandingOrderDetailSerializer(serializers.ModelSerializer):
    """Standing order detail serializer."""

    class Meta:
        """Meta class."""

        model = StandingOrderDetail
        fields = ['id', 'product', 'quantity']

class StandingOrderSerializer(serializers.ModelSerializer):
    """Standing order serializer."""

    details = StandingOrderDetailSerializer(many=True)

    class Meta:
        """Meta class."""

        model = StandingOrder
        fields = ['id', 'customer', 'day_of_week', 'details']

    def create(self, validated_data):
        """Create a standing order."""
        details_data = validated_data.pop('details')
        standing_order = StandingOrder.objects.create(**validated_data)
        for detail_data in details_data:
            StandingOrderDetail.objects.create(standing_order=standing_order, **detail_data)
        return standing_order

    def update(self, instance, validated_data):
        """Update a standing order."""
        details_data = validated_data.pop('details')
        instance.customer = validated_data.get('customer', instance.customer)
        instance.day_of_week = validated_data.get('day_of_week', instance.day_of_week)
        instance.save()

        instance.details.all().delete()
        for detail_data in details_data:
            StandingOrderDetail.objects.create(standing_order=instance, **detail_data)
        return instance
