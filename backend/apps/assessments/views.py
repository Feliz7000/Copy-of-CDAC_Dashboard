"""
API views for horizontal score matrix operations.
"""
import io

import pandas as pd
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.models import AuditLog
from apps.assessments.models import (
    Batch, CATEGORY_SCORE_MODEL_MAP, CategoryCourseMapping,
    StudentMaster, SystemConfig, TestMapping,
)
from apps.assessments.serializers import DynamicScoreSerializer


class ScoreDetailView(APIView):
    """GET + PUT /api/assessments/scores/{category_code}/{prn}/"""

    def _validate_scope(self, category_code, prn):
        model = CATEGORY_SCORE_MODEL_MAP.get(category_code.upper())
        if not model:
            return None, None, Response(
                {'error': 'Invalid category code'},
                status=status.HTTP_404_NOT_FOUND,
            )

        student = get_object_or_404(StudentMaster, prn=prn)

        mapping = CategoryCourseMapping.objects.filter(
            category_id=category_code.upper(),
            course_id=student.course_id,
            is_active=True,
        ).exists()

        if not mapping:
            return None, None, Response(
                {
                    'error': (
                        f'Category {category_code} is not applicable '
                        f'to course {student.course_id}'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return model, student, None

    def get(self, request, category_code, prn):
        model, student, error_response = self._validate_scope(category_code, prn)
        if error_response:
            return error_response

        try:
            batch_name = SystemConfig.get_active_batch()
        except SystemConfig.DoesNotExist:
            return Response(
                {'error': 'No active batch set. Contact administrator.'},
                status=503,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=503)

        score_record, _created = model.objects.get_or_create(prn=student)

        serializer = DynamicScoreSerializer(
            score_record,
            context={
                'category_code': category_code.upper(),
                'batch_name': batch_name,
            },
        )
        return Response(serializer.data)

    def put(self, request, category_code, prn):
        model, student, error_response = self._validate_scope(category_code, prn)
        if error_response:
            return error_response

        try:
            batch_name = SystemConfig.get_active_batch()
        except SystemConfig.DoesNotExist:
            return Response(
                {'error': 'No active batch set. Contact administrator.'},
                status=503,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=503)

        with transaction.atomic():
            score_record, _created = model.objects.select_for_update().get_or_create(prn=student)

            serializer = DynamicScoreSerializer(
                data=request.data,
                context={
                    'category_code': category_code.upper(),
                    'batch_name': batch_name,
                },
            )
            serializer.is_valid(raise_exception=True)

            col_to_attr = {
                f.column: f.attname
                for f in score_record._meta.fields
                if hasattr(f, 'column')
            }

            old_values = {}
            for db_col in serializer.validated_data.keys():
                attr = col_to_attr.get(db_col, db_col)
                old_values[db_col] = str(getattr(score_record, attr, None))

            for db_col, value in serializer.validated_data.items():
                attr = col_to_attr.get(db_col, db_col)
                setattr(score_record, attr, value)

            score_record.save()

            response_serializer = DynamicScoreSerializer(
                score_record,
                context={
                    'category_code': category_code.upper(),
                    'batch_name': batch_name,
                },
            )

            new_values = {f: str(v) for f, v in serializer.validated_data.items()}
            AuditLog.log_action(
                user_id=request.user.id if request.user.is_authenticated else 0,
                action='UPDATE',
                model_name=model.__name__,
                object_id=prn,
                changes={
                    'prn': prn,
                    'category_code': category_code.upper(),
                    'batch_name': batch_name,
                    'old_values': old_values,
                    'new_values': new_values,
                },
                ip_address=request.META.get('REMOTE_ADDR'),
            )

            return Response(response_serializer.data, status=status.HTTP_200_OK)


class TestMappingListView(APIView):
    """GET /api/assessments/test-mappings/{batch_name}/{category_code}/"""

    def get(self, request, batch_name, category_code):
        mappings = TestMapping.objects.filter(
            batch_name=batch_name,
            category_code=category_code.upper(),
            is_active=True,
        ).order_by('sequence')

        data = [
            {
                'id': tm.id,
                'logical_name': tm.logical_name,
                'column_slot': tm.column_slot,
                'max_marks': tm.max_marks,
                'sequence': tm.sequence,
            }
            for tm in mappings
        ]
        return Response(data)


class CategoryForCourseView(APIView):
    """GET /api/assessments/categories/for-course/{course_code}/"""

    def get(self, request, course_code):
        mappings = CategoryCourseMapping.objects.filter(
            course_id=course_code,
            is_active=True,
        ).select_related('category')

        data = [
            {
                'category_code': cm.category.category_code,
                'category_name': cm.category.category_name,
                'scaled_marks': cm.category.scaled_marks,
                'no_of_subtests': cm.category.no_of_subtests,
            }
            for cm in mappings
        ]
        return Response(data)


class ScoreBatchView(APIView):
    """GET /api/assessments/scores/batch/{category_code}/{course_code}/{batch_name}/"""

    def get(self, request, category_code, course_code, batch_name):
        model = CATEGORY_SCORE_MODEL_MAP.get(category_code.upper())
        if not model:
            return Response({'error': 'Invalid category code'}, status=status.HTTP_404_NOT_FOUND)

        if not batch_name:
            try:
                batch_name = SystemConfig.get_active_batch()
            except SystemConfig.DoesNotExist:
                return Response(
                    {'error': 'No active batch set. Contact administrator.'},
                    status=503,
                )
            except ValueError as e:
                return Response({'error': str(e)}, status=503)

        if not Batch.objects.filter(batch_name=batch_name).exists():
            return Response(
                {'error': f"Batch '{batch_name}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        students = StudentMaster.objects.filter(
            batch_id=batch_name,
            course_id=course_code,
            is_active=True,
        )

        score_records = model.objects.filter(prn__in=students).select_related('prn')
        score_map = {sr.prn_id: sr for sr in score_records}

        results = []
        for student in students:
            record = score_map.get(student.prn) or model(prn=student)
            serializer = DynamicScoreSerializer(
                record,
                context={
                    'category_code': category_code.upper(),
                    'batch_name': batch_name,
                },
            )
            results.append(serializer.data)

        return Response(results)


class ScoreTemplateView(APIView):
    """GET /api/assessments/scores/template/{category_code}/{course_code}/{batch_name}/"""

    def get(self, request, category_code, course_code, batch_name):
        if not batch_name:
            try:
                batch_name = SystemConfig.get_active_batch()
            except SystemConfig.DoesNotExist:
                return Response(
                    {'error': 'No active batch set. Contact administrator.'},
                    status=503,
                )
            except ValueError as e:
                return Response({'error': str(e)}, status=503)

        if not Batch.objects.filter(batch_name=batch_name).exists():
            return Response(
                {'error': f"Batch '{batch_name}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        students = StudentMaster.objects.filter(
            batch_id=batch_name,
            course_id=course_code,
            is_active=True,
        ).order_by('prn')

        mappings = TestMapping.objects.filter(
            batch_name=batch_name,
            category_code=category_code.upper(),
            is_active=True,
        ).order_by('sequence')

        data = []
        for student in students:
            row = {
                'prn': student.prn,
                'student_name': student.student_full_name,
                'category_code': category_code.upper(),
                'batch_name': batch_name,
            }
            for tm in mappings:
                row[tm.logical_name] = ''
            data.append(row)

        df = pd.DataFrame(data)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='MarksMatrix')

        buffer.seek(0)
        filename = f'Template_{category_code}_{batch_name.replace("/", "_")}.xlsx'
        response = HttpResponse(
            buffer.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
