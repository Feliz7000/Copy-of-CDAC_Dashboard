"""
Serializers for Analytics models (views and audit log)
"""
from rest_framework import serializers
from apps.analytics.models import (
    StudentCategoryScore, StudentGrandTotal, StudentScoresByDate,
    ExamScheduleWithDates, MonthlyActivityBreakdown, AuditLog
)


class StudentCategoryScoreSerializer(serializers.ModelSerializer):
    """Serializer for v_student_category_scores view"""
    class Meta:
        model = StudentCategoryScore
        fields = (
            'prn', 'full_name', 'centre_code', 'course_code',
            'enroll_year', 'batch_month', 'category_code', 'category_name',
            'original_total', 'scaled_total', 'raw_score', 'scaled_score'
        )


class StudentGrandTotalSerializer(serializers.ModelSerializer):
    """Serializer for v_student_grand_total view"""
    class Meta:
        model = StudentGrandTotal
        fields = (
            'prn', 'full_name', 'centre_code', 'course_code',
            'enroll_year', 'batch_month', 'grand_total', 'grade', 'description'
        )


class StudentScoresByDateSerializer(serializers.ModelSerializer):
    """Serializer for v_student_scores_by_date view"""
    class Meta:
        model = StudentScoresByDate
        fields = (
            'score_id', 'prn', 'full_name', 'tprn', 'sub_test_name',
            'category_code', 'exam_date', 'exam_month', 'exam_year',
            'month_label', 'score', 'is_absent', 'max_marks'
        )


class ExamScheduleWithDatesSerializer(serializers.ModelSerializer):
    """Serializer for v_exam_schedule_with_dates view"""
    class Meta:
        model = ExamScheduleWithDates
        fields = (
            'schedule_id', 'tprn', 'sub_test_name', 'category_code',
            'scheduled_date', 'scheduled_month', 'scheduled_year',
            'month_label', 'venue', 'is_confirmed'
        )


class MonthlyActivityBreakdownSerializer(serializers.ModelSerializer):
    """Serializer for v_monthly_activity_breakdown view"""
    class Meta:
        model = MonthlyActivityBreakdown
        fields = (
            'prn', 'full_name', 'tprn', 'sub_test_name', 'category_code',
            'month_label', 'exam_month', 'attempts_in_month', 'marks_in_month'
        )


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog"""
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = (
            'id', 'user_id', 'action', 'action_display', 'model_name',
            'object_id', 'changes', 'ip_address', 'created_at'
        )
        read_only_fields = ('id', 'created_at')
