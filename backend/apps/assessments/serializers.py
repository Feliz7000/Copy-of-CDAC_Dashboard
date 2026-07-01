"""
Serializers for Assessment models.
"""
from decimal import Decimal, InvalidOperation

from rest_framework import serializers

from apps.assessments.models import (
    Centre, Course, Batch, MainCategory, SubTest,
    StudentMaster, StudentTestScore, ExamSchedule, GradeScale, TestMapping,
)


# ==================== LOOKUP TABLE SERIALIZERS ====================

class CentreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Centre
        fields = ('centre_code', 'centre_name', 'is_active')


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('course_code', 'course_name', 'is_active')


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ('batch_name', 'batch_month', 'batch_year', 'is_active')


# ==================== MAIN CATEGORY SERIALIZER ====================

class MainCategorySerializer(serializers.ModelSerializer):
    active_subtest_count = serializers.SerializerMethodField(read_only=True)
    max_marks = serializers.DecimalField(
        source='max_marks_per_subtest',
        max_digits=8,
        decimal_places=2,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = MainCategory
        fields = (
            'category_code', 'category_name', 'description',
            'max_marks_per_subtest', 'max_marks', 'no_of_subtests',
            'scaled_marks', 'is_active', 'created_at', 'updated_at',
            'active_subtest_count',
        )
        read_only_fields = ('created_at', 'updated_at', 'active_subtest_count')

    def get_active_subtest_count(self, obj):
        return SubTest.objects.filter(
            category_code=obj.category_code,
            is_active=True,
        ).count()


# ==================== SUBTEST SERIALIZER ====================

class SubTestSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category_code.category_name', read_only=True
    )
    centre_name = serializers.CharField(
        source='centre_code.centre_name', read_only=True
    )
    course_name = serializers.CharField(
        source='course_code.course_name', read_only=True
    )
    batch_month = serializers.CharField(
        source='batch_name.batch_month', read_only=True
    )

    class Meta:
        model = SubTest
        fields = (
            'tprn', 'category_code', 'category_name', 'subtest_name',
            'centre_code', 'centre_name', 'course_code', 'course_name',
            'batch_name', 'batch_month', 'max_marks', 'test_date',
            'is_active', 'created_at', 'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')


# ==================== STUDENT MASTER SERIALIZER ====================

class StudentMasterSerializer(serializers.ModelSerializer):
    centre_code = serializers.CharField(source='centre_id', read_only=True)
    centre_name = serializers.CharField(source='centre.centre_name', read_only=True)
    course_code = serializers.CharField(source='course_id', read_only=True)
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    batch_name = serializers.CharField(source='batch_id', read_only=True)

    class Meta:
        model = StudentMaster
        fields = (
            'prn', 'student_full_name',
            'centre', 'centre_code', 'centre_name',
            'course', 'course_code', 'course_name',
            'batch', 'batch_name',
            'is_active', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'centre_code', 'centre_name',
            'course_code', 'course_name',
            'batch_name', 'created_at', 'updated_at',
        )


# ==================== STUDENT TEST SCORE SERIALIZER ====================

class StudentTestScoreSerializer(serializers.ModelSerializer):
    tprn_name = serializers.CharField(
        source='tprn.subtest_name', read_only=True
    )
    student_name = serializers.CharField(
        source='prn.student_full_name', read_only=True
    )
    max_marks = serializers.DecimalField(
        source='tprn.max_marks', read_only=True, max_digits=8, decimal_places=2
    )

    class Meta:
        model = StudentTestScore
        fields = (
            'score_id', 'tprn', 'tprn_name', 'prn', 'student_name',
            'subtest_name', 'category_code', 'batch_name',
            'score', 'is_absent', 'exam_date', 'max_marks',
            'is_active', 'created_at', 'updated_at',
        )
        read_only_fields = ('score_id', 'created_at', 'updated_at')


class ExamScheduleSerializer(serializers.ModelSerializer):
    tprn_name = serializers.CharField(source='tprn.subtest_name', read_only=True)

    class Meta:
        model = ExamSchedule
        fields = (
            'schedule_id', 'tprn', 'tprn_name', 'scheduled_date',
            'venue', 'notes', 'is_confirmed',
        )
        read_only_fields = ('schedule_id',)


class GradeScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeScale
        fields = ('grade', 'min_marks', 'max_marks', 'description')


class TestMappingSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category_code.category_name', read_only=True)

    class Meta:
        model = TestMapping
        fields = (
            'id', 'batch_name',
            'category_code', 'category_name', 'logical_name',
            'column_slot', 'max_marks', 'sequence', 'is_active',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class DynamicScoreSerializer(serializers.Serializer):
    """
    Dynamic serializer that translates physical columns (test_01…test_NN)
    to logical names from TestMapping.
    """

    def _get_db_col_to_attr_map(self, model_instance):
        return {
            f.column: f.attname
            for f in model_instance._meta.fields
            if hasattr(f, 'column')
        }

    def to_representation(self, instance):
        category_code = self.context.get('category_code')
        student = instance.prn
        batch_name = student.batch_id

        mappings = TestMapping.objects.filter(
            batch_name=batch_name,
            category_code=category_code,
            is_active=True,
        ).select_related('category_code').order_by('sequence')

        col_to_attr = self._get_db_col_to_attr_map(instance)

        scores = {}
        for tm in mappings:
            attr_name = col_to_attr.get(tm.column_slot, tm.column_slot)
            val = getattr(instance, attr_name, None)
            scores[tm.logical_name] = float(val) if val is not None else None

        return {
            'prn': student.prn,
            'category_code': category_code,
            'category_name': mappings[0].category_code.category_name if mappings.exists() else '',
            'scores': scores,
            'last_updated': instance.updated_at.isoformat() if instance.updated_at else None,
        }

    def to_internal_value(self, data):
        scores_payload = data.get('scores', {})
        if not isinstance(scores_payload, dict):
            raise serializers.ValidationError({'scores': 'Must be an object.'})

        category_code = self.context.get('category_code')
        batch_name = self.context.get('batch_name')

        mappings = TestMapping.objects.filter(
            batch_name=batch_name,
            category_code=category_code,
            is_active=True,
        )

        reverse_map = {tm.logical_name: (tm.column_slot, tm.max_marks) for tm in mappings}

        validated_scores = {}
        for logical_name, value in scores_payload.items():
            if logical_name not in reverse_map:
                raise serializers.ValidationError({
                    'error': (
                        f"Unknown test: '{logical_name}' for category '{category_code}' "
                        f"in batch '{batch_name}'"
                    ),
                })

            column_slot, max_marks = reverse_map[logical_name]

            if value is not None:
                try:
                    val_decimal = Decimal(str(value))
                    if val_decimal > max_marks:
                        raise serializers.ValidationError({
                            'error': f"'{logical_name}' score {value} exceeds max marks {max_marks}",
                        })
                    if val_decimal < 0:
                        raise serializers.ValidationError({
                            'error': f"'{logical_name}' score cannot be negative.",
                        })
                    validated_scores[column_slot] = val_decimal
                except (InvalidOperation, ValueError):
                    raise serializers.ValidationError({
                        'error': f"Invalid score value for '{logical_name}'",
                    })
            else:
                validated_scores[column_slot] = None

        return validated_scores
