"""
ViewSets for Analytics models and views
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta, date

from config.permissions import IsAdmin, IsFaculty
from apps.analytics.models import (
    StudentCategoryScore, StudentGrandTotal, StudentScoresByDate,
    ExamScheduleWithDates, MonthlyActivityBreakdown, AuditLog
)
from apps.users.models import User
from apps.assessments.models import StudentMaster, SubTest, Course, Batch
from .serializers import (
    StudentCategoryScoreSerializer, StudentGrandTotalSerializer,
    StudentScoresByDateSerializer, ExamScheduleWithDatesSerializer,
    MonthlyActivityBreakdownSerializer, AuditLogSerializer
)


class StudentCategoryScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for StudentCategoryScore view
    Shows student scores aggregated by category
    
    - list: Get all category scores (filtered by user role)
    - retrieve: Get category scores for specific student
    """
    queryset = StudentCategoryScore.objects.all()
    serializer_class = StudentCategoryScoreSerializer
    lookup_field = 'prn'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['centre_code', 'course_code', 'category_code', 'enroll_year', 'batch_month']
    search_fields = ['prn', 'full_name', 'category_name']
    ordering_fields = ['prn', 'scaled_score', 'raw_score']
    ordering = ['prn']
    
    def get_queryset(self):
        """Filter based on user role"""
        user = self.request.user
        if not user.is_authenticated:
            return StudentCategoryScore.objects.none()
        
        queryset = StudentCategoryScore.objects.all()
        
        # Admin sees all
        if user.role == 'admin':
            return queryset
        
        # HOD sees their courses
        if user.role == 'hod':
            courses = user.get_hod_course_list()
            return queryset.filter(course_code__in=courses)
        
        # Faculty sees all
        if user.role == 'faculty':
            return queryset
        
        # Students see only themselves
        if user.role == 'student':
            return queryset.filter(prn=user.prn)
        
        return StudentCategoryScore.objects.none()


class StudentGrandTotalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for StudentGrandTotal view
    Shows overall grades and totals per student
    
    - list: Get all student totals (filtered by user role)
    - retrieve: Get total for specific student
    """
    queryset = StudentGrandTotal.objects.all()
    serializer_class = StudentGrandTotalSerializer
    lookup_field = 'prn'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['centre_code', 'course_code', 'grade', 'enroll_year', 'batch_month']
    search_fields = ['prn', 'full_name', 'grade']
    ordering_fields = ['grand_total', 'prn']
    ordering = ['-grand_total']
    
    def get_queryset(self):
        """Filter based on user role"""
        user = self.request.user
        if not user.is_authenticated:
            return StudentGrandTotal.objects.none()
        
        queryset = StudentGrandTotal.objects.all()
        
        # Admin sees all
        if user.role == 'admin':
            return queryset
        
        # HOD sees their courses
        if user.role == 'hod':
            courses = user.get_hod_course_list()
            return queryset.filter(course_code__in=courses)
        
        # Faculty sees all
        if user.role == 'faculty':
            return queryset
        
        # Students see only themselves
        if user.role == 'student':
            return queryset.filter(prn=user.prn)
        
        return StudentGrandTotal.objects.none()


class StudentScoresByDateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for StudentScoresByDate view
    Shows scores with date components (month/year extracted)
    """
    queryset = StudentScoresByDate.objects.all()
    serializer_class = StudentScoresByDateSerializer
    lookup_field = 'score_id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['prn', 'tprn', 'exam_month', 'exam_year', 'is_absent']
    search_fields = ['prn', 'full_name', 'sub_test_name']
    ordering_fields = ['exam_date', 'exam_month', 'score']
    ordering = ['-exam_date']
    
    def get_queryset(self):
        """Filter based on user role"""
        user = self.request.user
        if not user.is_authenticated:
            return StudentScoresByDate.objects.none()
        
        queryset = StudentScoresByDate.objects.all()
        
        # Admin sees all
        if user.role == 'admin':
            return queryset
        
        # Faculty sees all
        if user.role == 'faculty':
            return queryset
        
        # Students see only their own
        if user.role == 'student':
            return queryset.filter(prn=user.prn)
        
        return StudentScoresByDate.objects.none()


class ExamScheduleWithDatesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for ExamScheduleWithDates view
    Shows exam schedules with date components
    """
    queryset = ExamScheduleWithDates.objects.all()
    serializer_class = ExamScheduleWithDatesSerializer
    lookup_field = 'schedule_id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tprn', 'scheduled_month', 'is_confirmed']
    search_fields = ['tprn', 'sub_test_name']
    ordering_fields = ['scheduled_date', 'is_confirmed']
    ordering = ['scheduled_date']


class MonthlyActivityBreakdownViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for MonthlyActivityBreakdown view
    Shows monthly exam activity per student
    """
    queryset = MonthlyActivityBreakdown.objects.all()
    serializer_class = MonthlyActivityBreakdownSerializer
    lookup_field = 'prn'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['prn', 'tprn', 'exam_month']
    search_fields = ['prn', 'full_name', 'sub_test_name']
    ordering_fields = ['exam_month', 'attempts_in_month', 'marks_in_month']
    ordering = ['-exam_month']
    
    def get_queryset(self):
        """Filter based on user role"""
        user = self.request.user
        if not user.is_authenticated:
            return MonthlyActivityBreakdown.objects.none()
        
        queryset = MonthlyActivityBreakdown.objects.all()
        
        # Admin sees all
        if user.role == 'admin':
            return queryset
        
        # Faculty sees all
        if user.role == 'faculty':
            return queryset
        
        # Students see only their own
        if user.role == 'student':
            return queryset.filter(prn=user.prn)
        
        return MonthlyActivityBreakdown.objects.none()


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for AuditLog
    Admin only - shows all audit trail entries
    
    - list: Get all audit log entries (Admin only)
    - retrieve: Get audit log detail (Admin only)
    - by_user: Get logs for specific user
    - by_model: Get logs for specific model
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_id', 'action', 'model_name']
    search_fields = ['user_id', 'model_name', 'object_id']
    ordering_fields = ['created_at', 'user_id', 'action']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Admin only"""
        user = self.request.user
        if user.is_authenticated and user.role == 'admin':
            return AuditLog.objects.all()
        return AuditLog.objects.none()
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Get audit logs for specific user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'detail': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logs = AuditLog.objects.filter(user_id=user_id).order_by('-created_at')
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_model(self, request):
        """Get audit logs for specific model"""
        model_name = request.query_params.get('model')
        if not model_name:
            return Response(
                {'detail': 'model parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logs = AuditLog.objects.filter(model_name=model_name).order_by('-created_at')
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)


class AnalyticsViewSet(viewsets.ViewSet):
    """
    Composite ViewSet for all analytics queries
    Combines data from multiple views for dashboard
    """
    
    @action(detail=False, methods=['get'])
    def student_summary(self, request):
        """Get complete summary for a student"""
        prn = request.query_params.get('prn')
        if not prn:
            return Response(
                {'detail': 'prn parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check permission
        if request.user.role == 'student' and request.user.prn != prn:
            return Response(
                {'detail': 'You do not have permission to view this student\'s summary.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            grand_total = StudentGrandTotal.objects.get(prn=prn)
            category_scores = StudentCategoryScore.objects.filter(prn=prn)
            monthly_activity = MonthlyActivityBreakdown.objects.filter(prn=prn)

            today = date.today()
            upcoming = ExamScheduleWithDates.objects.filter(
                scheduled_date__gte=today,
                is_confirmed=True,
            ).order_by('scheduled_date')[:5]

            return Response({
                'student': StudentGrandTotalSerializer(grand_total).data,
                'category_scores': StudentCategoryScoreSerializer(category_scores, many=True).data,
                'monthly_activity': MonthlyActivityBreakdownSerializer(monthly_activity, many=True).data,
                'upcoming_exams': ExamScheduleWithDatesSerializer(upcoming, many=True).data,
            })
        except StudentGrandTotal.DoesNotExist:
            return Response(
                {'detail': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def batch_performance(self, request):
        """Get performance metrics for entire batch/course"""
        centre_code = request.query_params.get('centre_code')
        course_code = request.query_params.get('course_code')
        enroll_year = request.query_params.get('enroll_year')
        
        queryset = StudentGrandTotal.objects.all()
        
        if centre_code:
            queryset = queryset.filter(centre_code=centre_code)
        if course_code:
            queryset = queryset.filter(course_code=course_code)
        if enroll_year:
            queryset = queryset.filter(enroll_year=enroll_year)
        
        serializer = StudentGrandTotalSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def system_overview(self, request):
        """Get high-level system statistics for admin dashboard"""
        if request.user.role != 'admin':
            return Response({'detail': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
            
        total_students = StudentMaster.objects.filter(is_active=True).count()
        total_staff = User.objects.exclude(role='student').count()
        total_courses = Course.objects.filter(is_active=True).count()
        total_batches = Batch.objects.filter(is_active=True).count()
        
        # Recent activity (last 7 days audit log counts)
        last_week = timezone.now() - timedelta(days=7)
        recent_logs = AuditLog.objects.filter(created_at__gte=last_week).count()
        
        return Response({
            'total_students': total_students,
            'total_staff': total_staff,
            'total_courses': total_courses,
            'total_batches': total_batches,
            'recent_activity_count': recent_logs,
            'system_status': 'Healthy'
        })

    @action(detail=False, methods=['get'], url_path='activity-trend')
    def activity_trend(self, request):
        """Daily audit-log counts for the last 7 days (admin only)."""
        if request.user.role != 'admin':
            return Response({'detail': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)

        today = timezone.now().date()
        start = today - timedelta(days=6)
        rows = (
            AuditLog.objects.filter(created_at__date__gte=start)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        count_by_day = {row['day']: row['count'] for row in rows}

        data = []
        for offset in range(7):
            day = start + timedelta(days=offset)
            data.append({
                'name': day.strftime('%a'),
                'score': count_by_day.get(day, 0),
            })

        return Response(data)

    @action(detail=False, methods=['get'], url_path='role-dashboard')
    def role_dashboard(self, request):
        """Aggregated dashboard stats and chart data for HOD / faculty."""
        user = request.user
        if user.role not in ('hod', 'faculty'):
            return Response({'detail': 'HOD or faculty access required.'}, status=status.HTTP_403_FORBIDDEN)

        totals_qs = StudentGrandTotal.objects.all()
        category_qs = StudentCategoryScore.objects.all()

        if user.role == 'hod':
            courses = user.get_hod_course_list()
            if not courses:
                return Response(self._empty_role_dashboard())
            totals_qs = totals_qs.filter(course_code__in=courses)
            category_qs = category_qs.filter(course_code__in=courses)

        total_students = totals_qs.count()
        if total_students == 0:
            return Response(self._empty_role_dashboard())

        avg_grand = float(totals_qs.aggregate(avg=Avg('grand_total'))['avg'] or 0)
        average_pct = round(avg_grand / 1500 * 100, 1)

        top_performers = totals_qs.filter(grand_total__gte=1275).count()
        at_risk = totals_qs.filter(grand_total__lt=600).count()

        category_chart = [
            {
                'name': row['category_name'] or row['category_code'],
                'total': round(float(row['avg'] or 0), 1),
            }
            for row in category_qs.values('category_code', 'category_name')
            .annotate(avg=Avg('scaled_score'))
            .order_by('category_code')
        ]

        course_chart = [
            {
                'name': row['course_code'],
                'total': round(float(row['avg'] or 0) / 1500 * 100, 1),
            }
            for row in totals_qs.values('course_code')
            .annotate(avg=Avg('grand_total'))
            .order_by('course_code')
        ]

        batch_trend = []
        for row in (
            totals_qs.values('enroll_year', 'batch_month')
            .annotate(avg=Avg('grand_total'))
            .order_by('enroll_year', 'batch_month')
        ):
            month = 'Feb' if row['batch_month'] == '02' else 'Aug'
            year = str(row['enroll_year'])[-2:]
            batch_trend.append({
                'name': f'{month} {year}',
                'score': round(float(row['avg'] or 0) / 1500 * 100, 1),
            })

        best_course = max(course_chart, key=lambda x: x['total']) if course_chart else None
        worst_course = min(course_chart, key=lambda x: x['total']) if course_chart else None

        return Response({
            'stats': {
                'total_students': total_students,
                'average_pct': average_pct,
                'top_performers': top_performers,
                'at_risk': at_risk,
                'best_course': best_course,
                'worst_course': worst_course,
            },
            'category_chart': category_chart,
            'course_chart': course_chart,
            'batch_trend': batch_trend,
        })

    @staticmethod
    def _empty_role_dashboard():
        return {
            'stats': {
                'total_students': 0,
                'average_pct': 0,
                'top_performers': 0,
                'at_risk': 0,
                'best_course': None,
                'worst_course': None,
            },
            'category_chart': [],
            'course_chart': [],
            'batch_trend': [],
        }
