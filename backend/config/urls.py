"""
Main URL configuration for Student Analytics Platform
Routes all app URLs and API endpoints.

Assessment ViewSets are registered under /api/assessments/ via apps.assessments.urls.
Users and analytics are registered in their respective app url modules.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/users/', include('apps.users.urls', namespace='users')),
    path('api/assessments/', include('apps.assessments.urls', namespace='assessments')),
    path('api/analytics/', include('apps.analytics.urls', namespace='analytics')),
    path('api/powerbi/', include('apps.powerbi.urls')),
]
