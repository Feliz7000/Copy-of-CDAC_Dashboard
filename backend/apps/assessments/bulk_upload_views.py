"""
Bulk upload API endpoints for SubTest, StudentMaster, and horizontal marks.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from config.permissions import IsAdmin
from apps.assessments.bulk_upload_handlers import (
    handle_subtest_bulk_upload,
    handle_student_master_bulk_upload,
    handle_horizontal_marks_bulk_upload,
    handle_test_mapping_bulk_upload
)


class BulkUploadViewSet(viewsets.ViewSet):
    """Handle bulk uploads for assessment data"""

    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        return [IsAdmin()]
    
    @action(detail=False, methods=['post'], url_path='subtests')
    def upload_subtests(self, request):
        """
        Bulk upload SubTests from Excel file
        
        Expected file: Excel with 'SubTest' sheet
        Columns: category_code, centre_code, course_code, batch_name, max_marks, date (optional)
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = handle_subtest_bulk_upload(request.FILES['file'])
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='student-master')
    def upload_student_master(self, request):
        """
        Bulk upload StudentMaster records from Excel file
        
        Expected file: Excel with 'StudentMaster' sheet
        Columns: prn, student_full_name, centre_name, course_name, batch_name
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = handle_student_master_bulk_upload(request.FILES['file'])
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='marks')
    def upload_marks(self, request):
        """
        Bulk upload marks into horizontal Score* tables from Excel.
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Switch to horizontal handler for the reformed schema
            result = handle_horizontal_marks_bulk_upload(request.FILES['file'])
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='student-template')
    def download_student_template(self, request):
        """Generate a template Excel file for StudentMaster upload"""
        import pandas as pd
        import io
        from django.http import HttpResponse
        
        # Create a DataFrame with the required headers
        df = pd.DataFrame(columns=[
            'prn', 'student_full_name', 'centre_name', 'course_name', 'batch_name'
        ])
        
        # Add sample data
        df.loc[0] = ['24020128001', 'John Doe', 'Mumbai HQ', 'Advanced Computing', 'Feb 2024']
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='StudentMaster')
            
        output.seek(0)
        
        # Return as response
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=student_master_template.xlsx'
        return response

    @action(detail=False, methods=['post'], url_path='test-mappings')
    def upload_test_mappings(self, request):
        """
        Bulk upload TestMapping records from Excel file
        
        Expected file: Excel with 'TestMapping' sheet
        Columns: centre_code, batch_name, category_code, logical_name, column_slot, max_marks, sequence
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = handle_test_mapping_bulk_upload(request.FILES['file'])
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='test-mapping-template')
    def download_test_mapping_template(self, request):
        """Generate a template Excel file for TestMapping upload"""
        import pandas as pd
        import io
        from django.http import HttpResponse
        
        # Create a DataFrame with the required headers
        df = pd.DataFrame(columns=[
            'centre_code', 'batch_name', 'category_code', 'logical_name', 'column_slot', 'max_marks', 'sequence'
        ])
        
        # Add sample data
        df.loc[0] = ['403', 'Aug/24', 'CC', 'CCEE-M1', 'test_01', 100, 1]
        df.loc[1] = ['403', 'Aug/24', 'CC', 'CCEE-M2', 'test_02', 100, 2]
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='TestMapping')
            
        output.seek(0)
        
        # Return as response
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=test_mapping_template.xlsx'
        return response
