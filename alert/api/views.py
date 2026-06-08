import jwt
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta, timezone
from alert.utils import generate_custom_jwt
from alert.api.permissions import IsAuthenticatedCustom
from alert.api.serializer import AlertSerializer
from alert.models import Alert
from alert.api.pagination import AlertCursorPagination
from alert.services import CryptoPriceService


class CustomLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            token = generate_custom_jwt(user)

            return Response(token, status=status.HTTP_201_CREATED)
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class ProtectedDashboardApiView(APIView):
    permission_classes = [IsAuthenticatedCustom]

    def get(self, request):
        return Response({
            'Message': f'Welcome Back {request.user.username} your custom jwt token works flowlessly'
        })


class CustomTokenRefreshView(APIView):

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({'error': 'Refresh Token not valid'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = jwt.decode(
                refresh_token, settings.SECRET_TOKEN, algorithms=['HS256'])

            if payload.get('type') != 'refresh':
                return Response({'error': 'Invalid Token Type'}, status=status.HTTP_400_BAD_REQUEST)

            new_access_payload = {
                'user_id': payload['user_id'],
                'exp': datetime.now(timezone.utc) + timedelta(days=10),
                'type': 'access'
            }

            new_access_token = jwt.encode(new_access_payload,
                                          settings.SECRET_KEY, algorithm='HS256')

            return Response({'access': new_access_token}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Refresh token expired please login again'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({'error': 'Invalid Token'}, status=status.HTTP_401_UNAUTHORIZED)


class AlertCreateListView(APIView):

    permission_classes = [IsAuthenticatedCustom]
    pagination_class = AlertCursorPagination

    def get(self, request):
        alert = Alert.objects.filter(user=request.user)

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(alert, request, view=self)

        if page is not None:
            serializer = AlertSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AlertSerializer(alert, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AlertSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CryptoPriceUpdateTrigger(APIView):

    def post(self, request):
        crypto_symbol = request.data.get('crypto_symbol', '').upper()

        if not crypto_symbol:
            return Response({'error': 'Missing crypto symbol in response'}, status=status.HTTP_400_BAD_REQUEST)

        current_price = CryptoPriceService.get_live_crypto_price(crypto_symbol)

        if not current_price:
            return Response({
                'error': f'Could not fetch live price for {crypto_symbol} at moment.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        print(f'{crypto_symbol} latest live price on internet ${current_price}')

        alerts_above = Alert.objects.filter(
            crypto_symbol=crypto_symbol,
            condition='ABOVE',
            target_price__lte=current_price,
            is_active=True
        )

        alerts_below = Alert.objects.filter(
            crypto_symbol=crypto_symbol,
            condition='BELOW',
            target_price__gte=current_price,
            is_active=True
        )

        triggered_count = 0

        for alert in (alerts_above | alerts_below):
            alert.is_active = False
            alert.save()
            triggered_count += 1
            print(
                f"Alert Triggered: User {alert.user.username}'s alert for {crypto_symbol} hit {current_price}")

        return Response({
            'message': f'Live price Processed',
            'live_price_checked': current_price,
            'alert_triggered': triggered_count
        }, status=status.HTTP_200_OK)


class DeleteAlertView(generics.DestroyAPIView):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticatedCustom]

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user)
