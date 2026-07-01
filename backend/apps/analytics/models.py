"""
Analytics models for Student Analytics Platform
Includes view models (read-only) and AuditLog (managed by Django)
View models map to PostgreSQL database views
"""
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


# ============================================================================
# VIEW MODELS (Read-only from PostgreSQL views - managed=False)
# ============================================================================

class StudentCategoryScore(models.Model):
    """
    Read-only view model for v_student_category_scores
    Shows aggregated scores by category per student
    """
    prn = models.CharField(max_length=12, primary_key=True)
    full_name = models.CharField(max_length=150)
    centre_code = models.CharField(max_length=3)
    course_code = models.CharField(max_length=2)
    enroll_year = models.SmallIntegerField()
    batch_month = models.CharField(max_length=2)
    category_code = models.CharField(max_length=3)
    category_name = models.CharField(max_length=100)
    original_total = models.DecimalField(max_digits=8, decimal_places=2)
    scaled_total = models.DecimalField(max_digits=8, decimal_places=2)
    raw_score = models.DecimalField(max_digits=10, decimal_places=2)
    scaled_score = models.DecimalField(max_digits=10, decimal_places=4)
    
    class Meta:
        managed = False
        db_table = 'v_student_category_scores'
        verbose_name = 'Student Category Score'
        verbose_name_plural = 'Student Category Scores'


class StudentGrandTotal(models.Model):
    """
    Read-only view model for v_student_grand_total
    Shows overall grade and total marks per student
    """
    prn = models.CharField(max_length=12, primary_key=True)
    full_name = models.CharField(max_length=150)
    centre_code = models.CharField(max_length=3)
    course_code = models.CharField(max_length=2)
    enroll_year = models.SmallIntegerField()
    batch_month = models.CharField(max_length=2)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)
    grade = models.CharField(max_length=2, null=True)
    description = models.CharField(max_length=50, null=True)
    
    class Meta:
        managed = False
        db_table = 'v_student_grand_total'
        verbose_name = 'Student Grand Total'
        verbose_name_plural = 'Student Grand Totals'


class StudentScoresByDate(models.Model):
    """
    Read-only view model for v_student_scores_by_date
    Shows student scores with date breakdown (month/year extracted)
    """
    score_id = models.BigIntegerField(primary_key=True)
    prn = models.CharField(max_length=12)
    full_name = models.CharField(max_length=150)
    tprn = models.CharField(max_length=20)
    sub_test_name = models.CharField(max_length=100)
    category_code = models.CharField(max_length=3)
    exam_date = models.DateField()
    exam_month = models.DateField()
    exam_year = models.SmallIntegerField()
    month_label = models.CharField(max_length=20)
    score = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    is_absent = models.BooleanField()
    max_marks = models.DecimalField(max_digits=8, decimal_places=2)
    
    class Meta:
        managed = False
        db_table = 'v_student_scores_by_date'
        verbose_name = 'Student Scores By Date'
        verbose_name_plural = 'Student Scores By Date'


class ExamScheduleWithDates(models.Model):
    """
    Read-only view model for v_exam_schedule_with_dates
    Shows exam schedule with date breakdown
    """
    schedule_id = models.BigIntegerField(primary_key=True)
    tprn = models.CharField(max_length=20)
    sub_test_name = models.CharField(max_length=100)
    category_code = models.CharField(max_length=3)
    scheduled_date = models.DateField()
    scheduled_month = models.DateField()
    scheduled_year = models.SmallIntegerField()
    month_label = models.CharField(max_length=20)
    venue = models.CharField(max_length=150, null=True)
    is_confirmed = models.BooleanField()
    
    class Meta:
        managed = False
        db_table = 'v_exam_schedule_with_dates'
        verbose_name = 'Exam Schedule With Dates'
        verbose_name_plural = 'Exam Schedules With Dates'


class MonthlyActivityBreakdown(models.Model):
    """
    Read-only view model for v_monthly_activity_breakdown
    Shows monthly exam activity per student
    """
    prn = models.CharField(max_length=12, primary_key=True)
    full_name = models.CharField(max_length=150)
    tprn = models.CharField(max_length=20)
    sub_test_name = models.CharField(max_length=100)
    category_code = models.CharField(max_length=3)
    month_label = models.CharField(max_length=20)
    exam_month = models.DateField()
    attempts_in_month = models.IntegerField()
    marks_in_month = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        managed = False
        db_table = 'v_monthly_activity_breakdown'
        verbose_name = 'Monthly Activity Breakdown'
        verbose_name_plural = 'Monthly Activity Breakdowns'


# ============================================================================
# AUDIT LOG (Managed by Django - for Django migrations)
# ============================================================================

class AuditLog(models.Model):
    """
    Audit logging for compliance and tracking changes
    Tracks all CRUD operations on students, scores, schedules
    """
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
    ]
    
    user_id = models.IntegerField(
        help_text="User who performed the action"
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text="Action performed (CREATE, UPDATE, DELETE, VIEW)"
    )
    model_name = models.CharField(
        max_length=100,
        help_text="Model name (e.g., 'Student', 'StudentTestScore')"
    )
    object_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID of the object modified"
    )
    changes = models.JSONField(
        null=True,
        blank=True,
        help_text="JSON of field changes (old_value -> new_value)"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of requester"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of action"
    )
    
    class Meta:
        managed = True
        db_table = 'audit_log'
        verbose_name = 'Audit Log Entry'
        verbose_name_plural = 'Audit Log Entries'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['model_name']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_action_display()} {self.model_name} (ID: {self.object_id}) by user {self.user_id}"
    
    @classmethod
    def log_action(cls, user_id, action, model_name, object_id, changes=None, ip_address=None):
        """
        Helper method to create audit log entries
        
        Args:
            user_id: ID of user performing action
            action: Action type (CREATE, UPDATE, DELETE, VIEW)
            model_name: Name of model being modified
            object_id: ID of object
            changes: Dict of field changes
            ip_address: IP of requester
        """
        return cls.objects.create(
            user_id=user_id,
            action=action,
            model_name=model_name,
            object_id=object_id,
            changes=changes,
            ip_address=ip_address,
        )
