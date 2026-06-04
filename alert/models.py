from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Alert(models.Model):

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='alerts')
    crypto_symbol = models.CharField(max_length=15, db_index=True)
    target_price = models.DecimalField(max_digits=15, decimal_places=2)

    CONDITION_CHOICES = [
        ('ABOVE', 'Price goes Above'),
        ('BELOW', 'Price goes Below')
    ]

    condition = models.CharField(
        max_length=15, choices=CONDITION_CHOICES, default='ABOVE')

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    triggered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.crypto_symbol} {self.condition} {self.target_price}'
