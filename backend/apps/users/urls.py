"""
URL configuration for users app
"""
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from .bulk_upload import UserBulkUploadViewSet

app_name = 'users'

router = DefaultRouter()
router.register(r'bulk', UserBulkUploadViewSet, basename='user-bulk')
router.register(r'', UserViewSet, basename='user')

urlpatterns = router.urls
