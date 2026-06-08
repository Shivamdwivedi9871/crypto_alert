from django.urls import path
from alert.api.views import (
    CustomLoginView, ProtectedDashboardApiView, CustomTokenRefreshView, AlertCreateListView, CryptoPriceUpdateTrigger, DeleteAlertView,)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('dashboard/', ProtectedDashboardApiView.as_view(), name='dashboard'),
    path('token/refresh/', CustomTokenRefreshView.as_view(),
         name='custom_token_refresh'),
    path('alerts/', AlertCreateListView.as_view(), name='alert_create_list'),
    path('price-update/', CryptoPriceUpdateTrigger.as_view(),
         name='price_update_trigger'),
    path('<int:pk>/', DeleteAlertView.as_view(), name='alert-delete'),
]
