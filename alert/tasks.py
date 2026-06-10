from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import requests
from django.db import transaction
from .services import CryptoPriceService
from .models import Alert
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@shared_task(
    bind=True,
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300
)
def check_crypto_alert_task(self):
    print(f'CELERY_TASK: Checking crypto Price alerts........')

    alert_symbol = Alert.objects.filter(is_active=True).values_list(
        'crypto_symbol', flat=True).distinct()

    if not alert_symbol:
        return 'No Active Alert to check'

    for symbol in alert_symbol:
        current_price = None
        cache_key = f'live_crypto_price_{symbol.upper()}'
        cached_price = cache.get(cache_key)

        if cached_price:
            print(
                f'CACHED HIT! Price for {symbol} fetched smootly from Redis Cache...')
            current_price = cached_price
        else:
            print(
                f'CACHED MISS! Fetching price for {symbol} from CoinGeko API...')
            try:
                current_price = CryptoPriceService.get_live_crypto_price(
                    symbol)

                if not current_price:
                    raise Exception(
                        f'Celery Could not fetch current price for {symbol}')
                cache.set(cache_key, current_price, timeout=120)
                print(
                    f'Saved fresh price for {symbol} in Redis Cache for 60 seconds')

            except Exception as exe:
                print(f'API Error for {symbol}: {str(exe)}. Retrying task....')
                raise self.retry(exc=exe)

        print(f'CELERY LIVE DATA: {symbol} current price ${current_price}')

        alerts_to_notify = []
        with transaction.atomic():

            alert_above = Alert.objects.select_for_update().filter(
                crypto_symbol=symbol,
                condition='ABOVE',
                target_price__lte=current_price,
                is_active=True
            )
            for alert in alert_above:
                alert.is_active = False
                alert.save()
                alerts_to_notify.append(alert, 'crossed', 'above')

        with transaction.atomic():
            alert_below = Alert.objects.select_for_update().filter(
                crypto_symbol=symbol,
                condition='BELOW',
                target_price__gte=current_price,
                is_active=True
            )
            for alert in alert_below:
                alert.is_active = False
                alert.save()
                alerts_to_notify.append(alert, 'dropped', 'below')

        for alert, action_word, direction in alerts_to_notify:
            user_email = alert.user.email
            subject = f'CRYPTO ALERT: {symbol} {action_word} your target'
            message = f"Hello {alert.user.username}, \n\n Your alert for {symbol} has been triggered! Current price is ${current_price}. \n\n Thanks \nCoinGeko"

            # Email Dispatch
            try:
                send_mail(subject, message,
                          settings.DEFAULT_FROM_EMAIL, [user_email])
                print(f"Email Sent to {user_email} for {symbol}")
            except Exception as exe:
                print(f"Failed to send email to {user_email}: {str(exe)}")

            # Websocket
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'user_{alert.user.username}'{
                        'type': 'Send Notification',
                        'message': f'Liver Alert: {symbol} has {direction} your traget price of ${alert.target_price}! Current: ${current_price}'
                    }
                )
                print(f'Websocket Pushed to group: user_{alert.user.username}')
            except Exception as ws_err:
                print(f'Failed to Push Websocket alert: {str(ws_err)}')

    return f'Processed alerts for symbols: {list(alert_symbol)}'
