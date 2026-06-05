import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings


def generate_custom_jwt(user):

    access_payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.now(timezone.utc) + timedelta(days=7),
        'type': 'access'
    }

    access_token = jwt.encode(
        access_payload, settings.SECRET_KEY, algorithm='HS256')

    refresh_payload = {
        'user_id': user.id,
        'exp': datetime.now(timezone.utc) + timedelta(days=30),
        'type': 'refresh'
    }

    refresh_token = jwt.encode(
        refresh_payload, settings.SECRET_KEY, algorithm='HS256')

    return {
        'access': access_token,
        'refresh': refresh_token
    }
