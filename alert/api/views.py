import jwt
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta, timezone
from alert.utils import generate_custom_jwt
from alert.api.permissions import IsAuthenticatedCustom
from alert.api.serializer import AlertSerializer
from alert.models import Alert


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

    def get(self, request):
        alert = Alert.objects.filter(user=request.user)
        serializer = AlertSerializer(alert, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AlertSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
