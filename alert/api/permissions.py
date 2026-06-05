import jwt
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.contrib.auth.models import User


class IsAuthenticatedCustom(BasePermission):

    def has_permission(self, request, view):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            raise AuthenticationFailed('Token not valid')

        try:

            token = auth_header.split(' ')[1]

            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=['HS256'])

            if payload.get('type') != 'access':
                raise AuthenticationFailed('Invalid Token Type')

            request.user = User.objects.get(id=payload['user_id'])
            return True

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')

        except (jwt.InvalidTokenError, User.DoesNotExist):
            raise AuthenticationFailed('Invalid Token')
