"""
ViewSets for Assessment models.
Includes CRUD operations, filtering, TPRN auto-generation, and validation.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from config.permissions import (
    CanManageScores, IsAdmin, IsAnyAuthenticated, IsStaffOnly,
    IsAdminOrHOD,
)
from apps.assessments.models import (
    Batch, CATEGORY_SCORE_MODEL_MAP, Centre, Course, ExamSchedule,
    GradeScale, MainCategory, StudentMaster, StudentTestScore, SubTest,
    TestMapping,
)
from apps.assessments.serializers import (
    BatchSerializer, CentreSerializer, CourseSerializer, ExamScheduleSerializer,
    GradeScaleSerializer, MainCategorySerializer, StudentMasterSerializer,
    StudentTestScoreSerializer, SubTestSerializer, TestMappingSerializer,
)


def generate_tprn(category_code):
    """Generate TPRN in format: {CATEGORY_CODE}-{SEQ} (e.g. AP-001)."""
    active_count = SubTest.objects.filter(
        category_code=category_code,
        is_active=True,
    ).count()

    total_count = SubTest.objects.filter(category_code=category_code).count()

    try:
        main_cat = MainCategory.objects.get(
            category_code=category_code,
            is_active=True,
        )
    except MainCategory.DoesNotExist:
        raise ValidationError(f'Category {category_code} not found or inactive')

    if active_count >= main_cat.no_of_subtests:
        raise ValidationError(
            f'Cannot create more subtests for {category_code}. '
            f'Maximum {main_cat.no_of_subtests} allowed, '
            f'{active_count} currently active.'
        )

    next_seq = total_count + 1
    return f'{category_code}-{next_seq:03d}'


def validate_subtest_count(category_code):
    try:
        main_cat = MainCategory.objects.get(
            category_code=category_code,
            is_active=True,
        )
    except MainCategory.DoesNotExist:
        raise ValidationError(f'Category {category_code} not found')

    active_count = SubTest.objects.filter(
        category_code=category_code,
        is_active=True,
    ).count()

    if active_count > main_cat.no_of_subtests:
        raise ValidationError(
            f'Active subtests ({active_count}) exceed limit '
            f'({main_cat.no_of_subtests}) for category {category_code}'
        )


class CentreViewSet(viewsets.ModelViewSet):
    queryset = Centre.objects.filter(is_active=True)
    serializer_class = CentreSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['centre_code', 'is_active']
    search_fields = ['centre_code', 'centre_name']
    ordering_fields = ['centre_code', 'centre_name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAnyAuthenticated()]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course_code', 'is_active']
    search_fields = ['course_code', 'course_name']
    ordering_fields = ['course_code', 'course_name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAnyAuthenticated()]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.filter(is_active=True)
    serializer_class = BatchSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['batch_month', 'batch_year', 'is_active']
    search_fields = ['batch_name']
    ordering_fields = ['batch_year', 'batch_month']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAnyAuthenticated()]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class MainCategoryViewSet(viewsets.ModelViewSet):
    queryset = MainCategory.objects.filter(is_active=True)
    serializer_class = MainCategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category_code', 'is_active']
    search_fields = ['category_code', 'category_name']
    ordering_fields = ['category_code', 'category_name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAnyAuthenticated()]

    @transaction.atomic
    def perform_create(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise ValidationError(str(e))

    @transaction.atomic
    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise ValidationError(str(e))

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=['get'])
    def active_subtests(self, request, pk=None):
        category = self.get_object()
        active_count = SubTest.objects.filter(
            category_code=category.category_code,
            is_active=True,
        ).count()
        total_count = SubTest.objects.filter(
            category_code=category.category_code,
        ).count()

        return Response({
            'category_code': category.category_code,
            'category_name': category.category_name,
            'active_subtests': active_count,
            'total_subtests': total_count,
            'max_allowed': category.no_of_subtests,
            'can_add_more': active_count < category.no_of_subtests,
        })


class SubTestViewSet(viewsets.ModelViewSet):
    queryset = SubTest.objects.filter(is_active=True)
    serializer_class = SubTestSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category_code', 'centre_code', 'course_code', 'batch_name', 'is_active']
    search_fields = ['tprn', 'subtest_name']
    ordering_fields = ['tprn', 'category_code', 'created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrHOD()]
        return [IsAnyAuthenticated()]

    @transaction.atomic
    def perform_create(self, serializer):
        category_code = serializer.validated_data.get('category_code')
        if not category_code:
            raise ValidationError('category_code is required')
        tprn = generate_tprn(category_code.category_code)
        serializer.save(tprn=tprn)

    @transaction.atomic
    def perform_update(self, serializer):
        validate_subtest_count(serializer.instance.category_code.category_code)
        serializer.save()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=['post'])
    def validate_unique_combo(self, request):
        data = request.data
        required_fields = ['tprn', 'centre_code', 'course_code', 'batch_name']

        if not all(field in data for field in required_fields):
            return Response(
                {'error': f'Required fields: {required_fields}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exists = SubTest.objects.filter(
            tprn=data['tprn'],
            centre_code=data['centre_code'],
            course_code=data['course_code'],
            batch_name=data['batch_name'],
            is_active=True,
        ).exists()

        return Response({
            'exists': exists,
            'message': 'This test combination already exists' if exists else 'Combination is available',
        })


class StudentMasterViewSet(viewsets.ModelViewSet):
    queryset = StudentMaster.objects.filter(is_active=True)
    serializer_class = StudentMasterSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['centre', 'course', 'batch', 'is_active']
    search_fields = ['prn', 'student_full_name']
    ordering_fields = ['prn', 'student_full_name', 'created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAnyAuthenticated()]

    @transaction.atomic
    def perform_create(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise ValidationError(str(e))

    @transaction.atomic
    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise ValidationError(str(e))

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=['get'])
    def by_centre_course_batch(self, request):
        centre_code = request.query_params.get('centre_code')
        course_code = request.query_params.get('course_code')
        batch_name = request.query_params.get('batch_name')

        queryset = StudentMaster.objects.filter(is_active=True)
        if centre_code:
            queryset = queryset.filter(centre_id=centre_code)
        if course_code:
            queryset = queryset.filter(course_id=course_code)
        if batch_name:
            queryset = queryset.filter(batch_id=batch_name)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StudentTestScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only legacy normalized scores. Canonical marks live in horizontal Score* tables."""

    queryset = StudentTestScore.objects.filter(is_active=True)
    serializer_class = StudentTestScoreSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tprn', 'prn', 'category_code', 'batch_name', 'is_absent', 'is_active']
    search_fields = ['tprn__tprn', 'prn__prn', 'prn__student_full_name']
    ordering_fields = ['score', 'exam_date', 'created_at']
    permission_classes = [IsAnyAuthenticated]

    @action(detail=False, methods=['get'])
    def by_student(self, request):
        prn = request.query_params.get('prn')
        if not prn:
            return Response(
                {'error': 'prn parameter required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = StudentTestScore.objects.filter(prn__prn=prn, is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_test(self, request):
        tprn = request.query_params.get('tprn')
        if not tprn:
            return Response(
                {'error': 'tprn parameter required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = StudentTestScore.objects.filter(tprn__tprn=tprn, is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ExamScheduleViewSet(viewsets.ModelViewSet):
    queryset = ExamSchedule.objects.all()
    serializer_class = ExamScheduleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tprn', 'is_confirmed']
    search_fields = ['tprn__tprn']
    ordering_fields = ['scheduled_date', 'is_confirmed']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsStaffOnly()]
        return [IsAnyAuthenticated()]


class GradeScaleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GradeScale.objects.all()
    serializer_class = GradeScaleSerializer
    permission_classes = [IsAnyAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['grade', 'description']
    ordering_fields = ['min_marks', 'max_marks']


class TestMappingViewSet(viewsets.ModelViewSet):
    queryset = TestMapping.objects.filter(is_active=True)
    serializer_class = TestMappingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['batch_name', 'category_code', 'is_active']
    search_fields = ['logical_name', 'column_slot']
    ordering_fields = ['sequence', 'created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'bulk_delete']:
            return [IsAdminOrHOD()]
        return [IsAnyAuthenticated()]
        batch = data['batch_name']

        existing_count = TestMapping.objects.filter(
            batch_name=batch,
            category_code=category,
            is_active=True,
        ).count()

        limit = category.no_of_subtests
        if existing_count >= limit:
            raise ValidationError(
                f"Limit reached: Category '{category.category_name}' only allows {limit} subtests. "
                f'You already have {existing_count} active mappings for this batch.'
            )

        serializer.save()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            raise ValidationError('Please provide a list of IDs to delete.')

        TestMapping.objects.filter(id__in=ids).update(is_active=False)
        return Response({'success': True, 'deleted_count': len(ids)})


class BulkActionViewSet(viewsets.ViewSet):
    """Bulk data management (delete students, clear category scores)."""

    def get_permissions(self):
        return [IsStaffOnly()]

    @action(detail=False, methods=['post'], url_path='delete-students')
    def bulk_delete_students(self, request):
        course_code = request.data.get('course_code')
        batch_name = request.data.get('batch_name')

        if not course_code or not batch_name:
            return Response(
                {'error': 'course_code and batch_name are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        students = StudentMaster.objects.filter(
            course_id=course_code,
            batch_id=batch_name,
        )
        total_found = students.count()

        if total_found == 0:
            return Response({'message': 'No students found for this scope'}, status=status.HTTP_200_OK)

        deleted_count = 0
        protected_count = 0
        errors = []

        with transaction.atomic():
            for student in students:
                try:
                    student.delete()
                    deleted_count += 1
                except ProtectedError:
                    protected_count += 1
                except Exception as e:
                    errors.append(f'Error deleting {student.prn}: {e}')

        return Response({
            'total': total_found,
            'deleted': deleted_count,
            'protected': protected_count,
            'errors': errors,
            'message': (
                f'Successfully deleted {deleted_count} students. '
                f'{protected_count} were protected due to existing scores.'
            ),
        })

    @action(detail=False, methods=['post'], url_path='clear-scores')
    def bulk_clear_scores(self, request):
        category_code = request.data.get('category_code')
        course_code = request.data.get('course_code')
        batch_name = request.data.get('batch_name')

        if not all([category_code, course_code, batch_name]):
            return Response(
                {'error': 'category_code, course_code, and batch_name are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model = CATEGORY_SCORE_MODEL_MAP.get(category_code.upper())
        if not model:
            return Response(
                {'error': f'Invalid category code: {category_code}'},
                status=status.HTTP_404_NOT_FOUND,
            )

        students = StudentMaster.objects.filter(
            course_id=course_code,
            batch_id=batch_name,
            is_active=True,
        )

        if not students.exists():
            return Response(
                {'message': 'No active students found for this scope'},
                status=status.HTTP_200_OK,
            )

        deleted_count, _ = model.objects.filter(prn__in=students).delete()

        return Response({
            'cleared_count': deleted_count,
            'message': (
                f'Successfully cleared scores for {deleted_count} students '
                f'in category {category_code}.'
            ),
        })
