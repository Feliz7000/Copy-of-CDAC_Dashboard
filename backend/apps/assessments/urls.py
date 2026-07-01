"""URL routing for assessment endpoints."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.assessments.bulk_upload_views import BulkUploadViewSet
from apps.assessments.report_views import CCEEIAModuleReportView, PlacementReportView
from apps.assessments.views import (
    CategoryForCourseView,
    ScoreBatchView,
    ScoreDetailView,
    ScoreTemplateView,
    TestMappingListView,
)
from apps.assessments.viewsets import (
    BatchViewSet,
    BulkActionViewSet,
    CentreViewSet,
    CourseViewSet,
    ExamScheduleViewSet,
    GradeScaleViewSet,
    MainCategoryViewSet,
    StudentMasterViewSet,
    StudentTestScoreViewSet,
    SubTestViewSet,
    TestMappingViewSet,
)

router = DefaultRouter()
router.register(r'centres', CentreViewSet, basename='centre')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'batches', BatchViewSet, basename='batch')
router.register(r'main-categories', MainCategoryViewSet, basename='main-category')
router.register(r'subtests', SubTestViewSet, basename='subtest')
router.register(r'student-master', StudentMasterViewSet, basename='student-master')
router.register(r'test-scores', StudentTestScoreViewSet, basename='test-score')
router.register(r'test-mappings', TestMappingViewSet, basename='test-mapping')
router.register(r'bulk-actions', BulkActionViewSet, basename='bulk-action')
router.register(r'exam-schedules', ExamScheduleViewSet, basename='exam-schedule')
router.register(r'grade-scales', GradeScaleViewSet, basename='grade-scale')
router.register(r'bulk-upload', BulkUploadViewSet, basename='bulk-upload')

app_name = 'assessments'

urlpatterns = [
    path('scores/<str:category_code>/<str:prn>/', ScoreDetailView.as_view(), name='score-detail'),
    path(
        'test-mappings/<path:batch_name>/<str:category_code>/',
        TestMappingListView.as_view(),
        name='test-mapping-list',
    ),
    path(
        'categories/for-course/<str:course_code>/',
        CategoryForCourseView.as_view(),
        name='categories-for-course',
    ),
    path(
        'scores/batch/<str:category_code>/<str:course_code>/<path:batch_name>/',
        ScoreBatchView.as_view(),
        name='score-batch',
    ),
    path(
        'scores/template/<str:category_code>/<str:course_code>/<path:batch_name>/',
        ScoreTemplateView.as_view(),
        name='score-template',
    ),
    path('reports/placement/', PlacementReportView.as_view(), name='placement-report'),
    path('reports/ccee-ia-modules/', CCEEIAModuleReportView.as_view(), name='ccee-ia-modules'),
    path('', include(router.urls)),
]
