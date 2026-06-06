from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Alert, NotificationLogs


@receiver(post_save, sender=Alert)
def create_notification_on_trigger(sender, instance, created, **kwargs):
    if not created:

        if not instance.is_active:

            if not NotificationLogs.objects.filter(alert=instance).exists():
                message = f"Alert Hit: your alert for {instance.crypto_symbol} at price {instance.target_price} has been triggered"

                NotificationLogs.objects.create(
                    user=instance.user,
                    alert=instance,
                    message=message
                )

                print(
                    f'Signal Notification kog successfully created for user {instance.user.username}!')
