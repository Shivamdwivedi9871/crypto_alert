from django.urls import path
from alert.api.views import (
    CustomLoginView, ProtectedDashboardApiView, CustomTokenRefreshView, AlertCreateListView)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('dashboard/', ProtectedDashboardApiView.as_view(), name='dashboard'),
    path('token/refresh/', CustomTokenRefreshView.as_view(),
         name='custom_token_refresh'),
    path('alerts/', AlertCreateListView.as_view(), name='alert_create_list'),
]
