"""
Permission classes for role-based access control
"""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Only admin users can access"""
    message = "Only administrators can access this resource."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsHOD(BasePermission):
    """Only HOD users can access"""
    message = "Only Head of Department can access this resource."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'hod'


class IsFaculty(BasePermission):
    """Only faculty users can access"""
    message = "Only faculty members can access this resource."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'faculty'


class IsStudent(BasePermission):
    """Only student users can access"""
    message = "Only students can access this resource."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'student'


class IsAdminOrReadOnly(BasePermission):
    """Admin can do anything, others can only read"""
    message = "Only administrators can modify this resource."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user.role == 'admin'


class IsAdminOrSelf(BasePermission):
    """
    Admin can access anything, students can only access their own data
    """
    message = "You don't have permission to access this resource."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin can access anything
        if request.user.role == 'admin':
            return True
        
        # Students can only access their own data
        if request.user.role == 'student':
            # Check if object has prn attribute
            if hasattr(obj, 'prn'):
                return obj.prn == request.user.prn
            return False
        
        # HOD and Faculty can access their batch data
        if request.user.role in ['hod', 'faculty']:
            if hasattr(obj, 'course_code') and hasattr(obj, 'enroll_year'):
                # Would need to implement batch/course filtering
                return True
        
        return False


class CanManageScores(BasePermission):
    """
    Only admin and faculty can create/update scores
    Students can only view their own scores
    """
    message = "You don't have permission to manage scores."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin and faculty can do anything
        if request.user.role in ['admin', 'faculty', 'hod']:
            return True
        
        # Students can only view
        if request.user.role == 'student':
            return request.method in ['GET', 'HEAD', 'OPTIONS']
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Admin and faculty can do anything
        if request.user.role in ['admin', 'faculty', 'hod']:
            return True
        
        # Students can only view their own scores
        if request.user.role == 'student':
            if request.method in ['GET', 'HEAD', 'OPTIONS']:
                if hasattr(obj, 'prn'):
                    return obj.prn == request.user.prn
            return False
        
        return False


# ─────────────────────────────────────────────────────────
# Combined OR-style permissions (any of the listed roles)
# ─────────────────────────────────────────────────────────

class IsAnyAuthenticated(BasePermission):
    """Any authenticated user — admin, hod, faculty, or student."""
    message = "Authentication required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('admin', 'hod', 'faculty', 'student')
        )


class IsAdminOrHOD(BasePermission):
    """Admin or HOD only."""
    message = "Only administrators or HODs can access this resource."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('admin', 'hod')
        )


class IsStaffOnly(BasePermission):
    """Admin, HOD, or Faculty — NOT students."""
    message = "Only staff members (admin, HOD, faculty) can access this resource."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('admin', 'hod', 'faculty')
        )


class CanAccessPowerBIEmbed(BasePermission):
    """Admin, HOD, faculty, or student — any role that may open an embedded CDAC.pbix report."""
    message = "You don't have permission to access Power BI reports."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('admin', 'hod', 'faculty', 'student')
        )

