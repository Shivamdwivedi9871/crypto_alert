from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import requests
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

        alert_above = Alert.objects.filter(
            crypto_symbol=symbol,
            condition='ABOVE',
            target_price__lte=current_price,
            is_active=True
        )
        triggered_count = 0
        for alert in alert_above:
            user_email = alert.user.email
            subject = f'Crypto Alert: {symbol} crossed your target'
            message = f"Hello {alert.user.username}, \n\n Your alert for {symbol} has been triggered! Current price is ${current_price}, which is above your target price of ${alert.target_price}. \n\nThaqnks, \nCrypto System ALert"

            try:
                send_mail(subject, message,
                          settings.DEFAULT_FROM_EMAIL, [user_email])
                print(
                    f'Email Notification Sent Successfully to {user_email} for {symbol}')
            except Exception as exe:
                print(f'Failed to send email to {user_email}: {str(exe)}')

            alert.is_active = False
            triggered_count += 1
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'user_{alert.user.username}',
                    {
                        'type': 'Send Notification',
                        'message': f"🚨 LIVE ALERT: {symbol} has crossed your target price of ${alert.target_price}! Current: ${current_price}"
                    }
                )

                print(
                    f'Websocket Live Alert pushed to group: user_{alert.user.username}')

            except Exception as ws_err:
                print(f"⚠️ Failed to push WebSocket alert: {str(ws_err)}")
            alert.save()

        alert_below = Alert.objects.filter(
            crypto_symbol=symbol,
            condition='BELOW',
            target_price__gte=current_price,
            is_active=True
        )
        for alert in alert_below:
            user_email = alert.user.email
            subject = f'Crypto Alert: {symbol} Dropped your target'
            message = f"Hello {alert.user.username}, \n\n Your alert for {symbol} has been triggered! Current price is ${current_price}, which is below your target price of ${alert.target_price}. \n\nThaqnks, \nCrypto System ALert"

            try:
                send_mail(subject, message,
                          settings.DEFAULT_FROM_EMAIL, [user_email])
                print(
                    f'Email Notification Sent Successfully to {user_email} for {symbol}')
            except Exception as exc:
                print(f'Failed to send email to {user_email}: {str(exc)}')

            alert.is_active = False
            triggered_count += 1
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'user_{alert.user.username}',
                    {
                        'type': 'Send Notification',
                        'message': f"🚨 LIVE ALERT: {symbol} has crossed your target price of ${alert.target_price}! Current: ${current_price}"
                    }
                )

                print(
                    f'Websocket Live Alert pushed to group: user_{alert.user.username}')

            except Exception as ws_err:
                print(f"⚠️ Failed to push WebSocket alert: {str(ws_err)}")
            alert.save()

    #     for alert in (alert_above | alert_below):
    #         alert.is_active = False
    #         alert.save()
    #         triggered_count += 1
    #         print(
    #             f"CELERY HIT: User {alert.user.username}'s alert triggered for {symbol}")

    return f'Processed alerts for symbols: {list(alert_symbol)}'
