"""
User model for Student Analytics Platform
Extended Django User with role-based access control
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended Django User with role and optional PRN for students"""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('hod', 'Head of Department'),
        ('faculty', 'Faculty'),
        ('student', 'Student'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        help_text="User role for permission control"
    )
    prn = models.CharField(
        max_length=12,
        null=True,
        blank=True,
        unique=True,
        help_text="Student PRN (12 digits) - required for student role"
    )
    hod_courses = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Comma-separated course codes for HOD (e.g., '28,14,35')"
    )
    
    class Meta:
        app_label = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def get_hod_course_list(self):
        """Returns list of course codes for HOD users"""
        if self.hod_courses:
            return [c.strip() for c in self.hod_courses.split(',')]
        return []
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def is_hod(self):
        """Check if user is HOD"""
        return self.role == 'hod'
    
    def is_faculty(self):
        """Check if user is faculty"""
        return self.role == 'faculty'
    
    def is_student_user(self):
        """Check if user is a student"""
        return self.role == 'student'
