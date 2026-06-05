from rest_framework import serializers
from alert.models import Alert


class AlertSerializer(serializers.ModelSerializer):

    class Meta:
        model = Alert
        fields = ['id', 'crypto_symbol', 'target_price',
                  'condition', 'is_active', 'created_at']
        read_only_fields = ['id', 'is_active', 'created_at']

    def validate_crypto_symbol(self, value):
        return value.upper()
