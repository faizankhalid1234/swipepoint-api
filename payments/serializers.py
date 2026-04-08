from rest_framework import serializers


class ChargeSerializer(serializers.Serializer):
    """Request body matching SwipePoint charge API (all string fields)."""

    amount = serializers.CharField()
    currency = serializers.CharField()
    reference = serializers.CharField(max_length=255)

    firstname = serializers.CharField(max_length=128)
    lastname = serializers.CharField(max_length=128)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=32)

    cardName = serializers.CharField(max_length=128)
    cardNumber = serializers.CharField(max_length=32)
    cardCVV = serializers.CharField(max_length=8)
    expMonth = serializers.CharField(max_length=2)
    expYear = serializers.CharField(max_length=4)

    country = serializers.CharField(max_length=2)
    city = serializers.CharField(max_length=128)
    address = serializers.CharField()
    ip_address = serializers.CharField(max_length=64)
    zip_code = serializers.CharField(max_length=32)
    state = serializers.CharField(max_length=128)

    callback_url = serializers.URLField(max_length=2048)
    webhook_url = serializers.URLField(max_length=2048, required=False, allow_blank=True)

    def validate_currency(self, value: str) -> str:
        v = value.strip().upper()
        if len(v) < 3:
            raise serializers.ValidationError("Invalid currency code.")
        return v

    def validate_country(self, value: str) -> str:
        v = value.strip().upper()
        if len(v) != 2 or not v.isalpha():
            raise serializers.ValidationError("country must be a 2-letter ISO alpha-2 code.")
        return v
