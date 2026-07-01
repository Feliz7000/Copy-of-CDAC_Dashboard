"""
Serializers for User model
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name', 'role', 'prn')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, data):
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError({"password": "Passwords don't match."})
        return data
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details"""
    full_name = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'role', 'prn', 'hod_courses', 'is_active', 
            'date_joined', 'last_login', 'password'
        )
        read_only_fields = ('id', 'date_joined', 'last_login')
    
    def get_full_name(self, obj):
        """Return full name"""
        return obj.get_full_name()

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile with extended info"""
    hod_course_list = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'prn', 'hod_courses', 'hod_course_list', 'is_active'
        )
        read_only_fields = ('id',)
    
    def get_hod_course_list(self, obj):
        """Return parsed HOD course list"""
        return obj.get_hod_course_list()


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True, min_length=8)
    
    def validate(self, data):
        if data['new_password'] != data.pop('new_password2'):
            raise serializers.ValidationError({"new_password": "Passwords don't match."})
        return data
