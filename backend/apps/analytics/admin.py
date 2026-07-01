"""
Django admin configuration for analytics app
"""
from django.contrib import admin
from apps.analytics.models import (
    StudentCategoryScore, StudentGrandTotal, StudentScoresByDate,
    ExamScheduleWithDates, MonthlyActivityBreakdown, AuditLog
)


@admin.register(StudentCategoryScore)
class StudentCategoryScoreAdmin(admin.ModelAdmin):
    """Read-only admin for StudentCategoryScore view"""
    list_display = ('prn', 'full_name', 'category_name', 'raw_score', 'scaled_score')
    list_filter = ('centre_code', 'course_code', 'category_code', 'enroll_year')
    search_fields = ('prn', 'full_name', 'category_name')
    readonly_fields = (
        'prn', 'full_name', 'centre_code', 'course_code', 'enroll_year',
        'batch_month', 'category_code', 'category_name', 'original_total',
        'scaled_total', 'raw_score', 'scaled_score'
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StudentGrandTotal)
class StudentGrandTotalAdmin(admin.ModelAdmin):
    """Read-only admin for StudentGrandTotal view"""
    list_display = ('prn', 'full_name', 'grand_total', 'grade', 'description')
    list_filter = ('grade', 'centre_code', 'course_code', 'enroll_year')
    search_fields = ('prn', 'full_name', 'grade')
    readonly_fields = (
        'prn', 'full_name', 'centre_code', 'course_code', 'enroll_year',
        'batch_month', 'grand_total', 'grade', 'description'
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StudentScoresByDate)
class StudentScoresByDateAdmin(admin.ModelAdmin):
    """Read-only admin for StudentScoresByDate view"""
    list_display = ('score_id', 'prn', 'sub_test_name', 'exam_date', 'score', 'is_absent')
    list_filter = ('is_absent', 'exam_date', 'exam_month', 'exam_year')
    search_fields = ('prn', 'full_name', 'sub_test_name')
    readonly_fields = (
        'score_id', 'prn', 'full_name', 'tprn', 'sub_test_name',
        'category_code', 'exam_date', 'exam_month', 'exam_year',
        'month_label', 'score', 'is_absent', 'max_marks'
    )
    date_hierarchy = 'exam_date'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ExamScheduleWithDates)
class ExamScheduleWithDatesAdmin(admin.ModelAdmin):
    """Read-only admin for ExamScheduleWithDates view"""
    list_display = ('schedule_id', 'tprn', 'scheduled_date', 'venue', 'is_confirmed')
    list_filter = ('is_confirmed', 'scheduled_date', 'scheduled_month')
    search_fields = ('tprn', 'sub_test_name', 'venue')
    readonly_fields = (
        'schedule_id', 'tprn', 'sub_test_name', 'category_code',
        'scheduled_date', 'scheduled_month', 'scheduled_year',
        'month_label', 'venue', 'is_confirmed'
    )
    date_hierarchy = 'scheduled_date'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MonthlyActivityBreakdown)
class MonthlyActivityBreakdownAdmin(admin.ModelAdmin):
    """Read-only admin for MonthlyActivityBreakdown view"""
    list_display = ('prn', 'full_name', 'month_label', 'attempts_in_month', 'marks_in_month')
    list_filter = ('exam_month',)
    search_fields = ('prn', 'full_name', 'sub_test_name')
    readonly_fields = (
        'prn', 'full_name', 'tprn', 'sub_test_name', 'category_code',
        'month_label', 'exam_month', 'attempts_in_month', 'marks_in_month'
    )
    date_hierarchy = 'exam_month'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin for AuditLog"""
    list_display = ('created_at', 'user_id', 'action', 'model_name', 'object_id')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('user_id', 'model_name', 'object_id', 'ip_address')
    readonly_fields = ('id', 'created_at', 'user_id', 'action', 'model_name', 'object_id', 'changes', 'ip_address')
    fieldsets = (
        ('Action Details', {
            'fields': ('id', 'user_id', 'action', 'model_name', 'object_id')
        }),
        ('Changes', {
            'fields': ('changes',)
        }),
        ('Request Info', {
            'fields': ('ip_address', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
