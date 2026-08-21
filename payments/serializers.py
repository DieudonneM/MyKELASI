from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    booking_id = serializers.UUIDField(source="booking.public_id", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "public_id",
            "reference",
            "booking_id",
            "amount",
            "currency",
            "provider",
            "status",
            "created_at",
        )
        read_only_fields = fields
