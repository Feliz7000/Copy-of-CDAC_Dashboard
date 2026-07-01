"""
URL configuration for analytics app
"""
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    StudentCategoryScoreViewSet, StudentGrandTotalViewSet,
    StudentScoresByDateViewSet, ExamScheduleWithDatesViewSet,
    MonthlyActivityBreakdownViewSet, AuditLogViewSet, AnalyticsViewSet
)

app_name = 'analytics'

router = DefaultRouter()
router.register(r'category-scores', StudentCategoryScoreViewSet, basename='category-score')
router.register(r'grand-totals', StudentGrandTotalViewSet, basename='grand-total')
router.register(r'scores-by-date', StudentScoresByDateViewSet, basename='score-by-date')
router.register(r'exam-schedules', ExamScheduleWithDatesViewSet, basename='exam-schedule')
router.register(r'monthly-activity', MonthlyActivityBreakdownViewSet, basename='monthly-activity')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'', AnalyticsViewSet, basename='analytics')

urlpatterns = router.urls
