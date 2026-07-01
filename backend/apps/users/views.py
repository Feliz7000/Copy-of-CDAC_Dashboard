"""
ViewSets and API views for User management
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from config.permissions import IsAdmin
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User management
    
    - list: Get all users (Admin only)
    - create: Register new user (Admin only)
    - retrieve: Get user details
    - update: Update user (Admin or self)
    - destroy: Delete user (Admin only)
    - profile: Get current user profile (self)
    - change_password: Change password (self)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'list', 'destroy']:
            permission_classes = [IsAdmin]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter users based on role"""
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        
        # Admin sees all users
        if user.role == 'admin':
            return User.objects.all()
        
        # Others see only themselves
        return User.objects.filter(pk=user.pk)
    
    def get_serializer_class(self):
        """Choose serializer based on action"""
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        """Get current user profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """Change password"""
        user = request.user
        serializer = PasswordChangeSerializer(data=request.data)
        
        if serializer.is_valid():
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': ['Wrong password.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'detail': 'Password changed successfully.'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
