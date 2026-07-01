"""
Bulk upload handlers for reformed assessment system
Supports: SubTest, StudentMaster, StudentTestScore uploads
"""
import pandas as pd
from io import BytesIO
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from decimal import Decimal

from apps.assessments.models import (
    MainCategory, SubTest, Centre, Course, Batch,
    StudentMaster, StudentTestScore, TestMapping
)


class BulkUploadError:
    """Helper class to track upload errors"""
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.created_count = 0
        self.skipped_count = 0
    
    def add_error(self, row_num, message):
        self.errors.append(f"Row {row_num}: {message}")
    
    def add_warning(self, row_num, message):
        self.warnings.append(f"Row {row_num}: {message}")
    
    def to_dict(self):
        return {
            'success': len(self.errors) == 0,
            'created': self.created_count,
            'skipped': self.skipped_count,
            'errors': self.errors,
            'warnings': self.warnings,
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings)
        }


def normalize_batch_name(batch_val):
    """
    Prevents Pandas/Excel from turning 'Aug-24' into '2024-08-01 00:00:00'
    by detecting datetime-like values and forcing them to 'Mon/YY' format.
    """
    if pd.isna(batch_val) or batch_val == "":
        return ""
        
    if isinstance(batch_val, (pd.Timestamp, datetime)):
        return batch_val.strftime("%b/%y")
        
    val_str = str(batch_val).strip()
    
    # Sometimes Excel gives us stringified datetimes
    if len(val_str) >= 10 and '-' in val_str and ':' in val_str:
        try:
            dt = pd.to_datetime(val_str)
            return dt.strftime("%b/%y")
        except:
            pass
            
    # Normalize dash to slash if user typed "Aug-24" instead of "Aug/24"
    if len(val_str) == 6 and val_str[3] == '-':
        val_str = val_str[:3] + '/' + val_str[4:]
        
    return val_str


def read_excel_flexible(excel_file, possible_sheets, column_mapping, optional_mapping=None):
    """
    Tries multiple sheet names and maps columns flexibly
    """
    try:
        xls = pd.ExcelFile(excel_file)
    except Exception as e:
        raise ValidationError(f"Failed to open Excel file: {str(e)}")
        
    sheet_name = None
    for s in possible_sheets:
        if s in xls.sheet_names:
            sheet_name = s
            break
    
    if not sheet_name:
        raise ValidationError(f"Expected one of these sheets: {possible_sheets}. Found: {xls.sheet_names}")
    
    df = pd.read_excel(excel_file, sheet_name=sheet_name, keep_default_na=False)
    
    # Normalize current columns for easier mapping
    # "Full Name" -> "full_name"
    # "Category Code" -> "category_code"
    norm_cols = {str(c).lower().strip().replace(' ', '_'): c for c in df.columns}
    
    mapped_df = pd.DataFrame()
    
    # Map required columns
    for target, alternatives in column_mapping.items():
        found_col = None
        if target in norm_cols:
            found_col = norm_cols[target]
        else:
            for alt in alternatives:
                if alt in norm_cols:
                    found_col = norm_cols[alt]
                    break
        
        if found_col is None:
            raise ValidationError(f"Required column '{target}' not found in sheet '{sheet_name}'. Available: {list(df.columns)}")
        
        mapped_df[target] = df[found_col]

    # Map optional columns
    if optional_mapping:
        for target, alternatives in optional_mapping.items():
            found_col = None
            if target in norm_cols:
                found_col = norm_cols[target]
            else:
                for alt in alternatives:
                    if alt in norm_cols:
                        found_col = norm_cols[alt]
                        break
            
            if found_col is not None:
                mapped_df[target] = df[found_col]
            else:
                mapped_df[target] = None

    return mapped_df


# ==================== SUBTEST BULK UPLOAD ====================

def handle_subtest_bulk_upload(excel_file):
    """
    Upload SubTests from Excel file
    
    Expected columns:
    - category_code (must exist in MainCategory)
    - centre_code (must exist in Centre)
    - course_code (must exist in Course)
    - batch_name (must exist in Batch)
    - max_marks (float)
    - date (optional, YYYY-MM-DD format)
    - subtest_name (optional, auto-generated if not provided)
    
    Auto-generates TPRN in format: {CATEGORY_CODE}-{SEQ}
    """
    
    result = BulkUploadError()
    
    # Define flexible mapping
    possible_sheets = ['SubTest', 'SubTests', 'Tests', 'Test Definitions']
    required_mapping = {
        'category_code': ['category', 'cat_code', 'category_identifier'],
        'centre_code': ['centre', 'center_code', 'center'],
        'course_code': ['course', 'crs_code'],
        'batch_name': ['batch', 'batch_id'],
        'max_marks': ['marks', 'maximum_marks']
    }
    optional_mapping = {
        'test_date': ['date', 'exam_date', 'scheduled_date'],
        'subtest_name': ['name', 'test_name', 'sub_test_name']
    }
    
    try:
        df = read_excel_flexible(excel_file, possible_sheets, required_mapping, optional_mapping)
    except ValidationError as e:
        raise e
    except Exception as e:
        raise ValidationError(f"Excel parsing error: {str(e)}")
    
    with transaction.atomic():
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel row number (1-indexed, +1 for header)
            
            try:
                # Validate required fields
                category_code_str = str(row['category_code']).strip()
                centre_code = str(row['centre_code']).strip()
                course_code = str(row['course_code']).strip()
                batch_name = normalize_batch_name(row['batch_name'])
                max_marks = float(row['max_marks'])
                
                # Optional fields
                date_val = row['test_date']
                subtest_name = row['subtest_name']
                
                # Validate category exists
                try:
                    category = MainCategory.objects.get(
                        category_code=category_code_str,
                        is_active=True
                    )
                except MainCategory.DoesNotExist:
                    result.add_error(row_num, f"Category '{category_code_str}' not found or inactive")
                    result.skipped_count += 1
                    continue
                
                # Validate centre exists
                try:
                    Centre.objects.get(centre_code=centre_code, is_active=True)
                except Centre.DoesNotExist:
                    result.add_error(row_num, f"Centre '{centre_code}' not found or inactive")
                    result.skipped_count += 1
                    continue
                
                # Validate course exists
                try:
                    Course.objects.get(course_code=course_code, is_active=True)
                except Course.DoesNotExist:
                    result.add_error(row_num, f"Course '{course_code}' not found or inactive")
                    result.skipped_count += 1
                    continue
                
                # Validate batch exists
                try:
                    Batch.objects.get(batch_name=batch_name, is_active=True)
                except Batch.DoesNotExist:
                    result.add_error(row_num, f"Batch '{batch_name}' not found or inactive")
                    result.skipped_count += 1
                    continue
                
                # Parse date if provided
                exam_date = None
                date_val = row['test_date']
                if date_val and str(date_val).lower() != 'nan':
                    try:
                        exam_date = pd.to_datetime(date_val).date()
                    except:
                        result.add_warning(row_num, f"Invalid date format: '{date_val}', skipping")
                
                # Check if this combination already exists
                existing = SubTest.objects.filter(
                    category_code=category,
                    centre_code=centre_code,
                    course_code=course_code,
                    batch_name=batch_name,
                    is_active=True
                ).exists()
                
                if existing:
                    result.add_warning(
                        row_num,
                        f"Test for this combination already exists, skipping"
                    )
                    result.skipped_count += 1
                    continue
                
                # Check subtest count limit
                active_count = SubTest.objects.filter(
                    category_code=category,
                    is_active=True
                ).count()
                
                if active_count >= category.no_of_subtests:
                    result.add_error(
                        row_num,
                        f"Cannot add more subtests. Maximum {category.no_of_subtests} allowed, "
                        f"{active_count} already exist"
                    )
                    result.skipped_count += 1
                    continue
                
                # Generate TPRN
                next_seq = active_count + 1
                tprn = f"{category_code_str}-{next_seq:03d}"
                
                # Create SubTest
                subtest = SubTest.objects.create(
                    tprn=tprn,
                    category_code=category,
                    centre_code=centre_code,
                    course_code=course_code,
                    batch_name=batch_name,
                    max_marks=max_marks,
                    test_date=exam_date,
                    subtest_name=subtest_name or f"{category_code_str}-{next_seq:03d}",
                    is_active=True
                )
                
                # Also create a TestMapping record so horizontal uploads and marks UI
                # can immediately pick up this test. Use a column slot like 'test_01'.
                try:
                    col_slot = f"test_{next_seq:02d}"
                    TestMapping.objects.update_or_create(
                        batch_name_id=batch_name,
                        category_code=category,
                        column_slot=col_slot,
                        defaults={
                            'logical_name': subtest.subtest_name,
                            'max_marks': Decimal(str(max_marks)),
                            'sequence': next_seq,
                            'is_active': True
                        }
                    )
                except Exception as e:
                    # Don't fail the whole row for mapping creation; record a warning
                    result.add_warning(row_num, f"TestMapping not created: {str(e)}")

                result.created_count += 1
            
            except Exception as e:
                result.add_error(row_num, str(e))
                result.skipped_count += 1
    
    return result.to_dict()


# ==================== STUDENT MASTER BULK UPLOAD ====================

def handle_student_master_bulk_upload(excel_file):
    """
    Upload StudentMaster records from Excel file
    
    Expected columns:
    - prn (string, unique)
    - student_full_name
    - centre_name (will be matched to Centre, derives centre_code)
    - course_name (will be matched to Course, derives course_code)
    - batch_name (will be matched to Batch)
    
    Derived fields auto-populated in model.save()
    """
    
    result = BulkUploadError()
    
    # Define flexible mapping
    possible_sheets = ['StudentMaster', 'Students Master', 'Student Master', 'Students']
    required_mapping = {
        'prn': ['student_prn', 'id'],
        'student_full_name': ['full_name', 'student_name', 'name'],
        'centre_name': ['centre', 'center_name', 'center'],
        'course_name': ['course', 'course_title'],
        'batch_name': ['batch', 'batch_label']
    }
    
    try:
        df = read_excel_flexible(excel_file, possible_sheets, required_mapping)
    except ValidationError as e:
        raise e
    except Exception as e:
        raise ValidationError(f"Excel parsing error: {str(e)}")
    
    with transaction.atomic():
        for idx, row in df.iterrows():
            row_num = idx + 2
            
            try:
                prn = str(row['prn']).strip()
                student_full_name = str(row['student_full_name']).strip()
                centre_name = str(row['centre_name']).strip()
                course_name = str(row['course_name']).strip()
                batch_name = normalize_batch_name(row['batch_name'])
                
                # Check if PRN already exists
                if StudentMaster.objects.filter(prn=prn, is_active=True).exists():
                    result.add_warning(row_num, f"PRN '{prn}' already exists, skipping")
                    result.skipped_count += 1
                    continue
                
                # Look up centre by name
                try:
                    centre = Centre.objects.get(centre_name=centre_name, is_active=True)
                except Centre.DoesNotExist:
                    result.add_error(row_num, f"Centre '{centre_name}' not found")
                    result.skipped_count += 1
                    continue
                
                # Look up course by name
                try:
                    course = Course.objects.get(course_name=course_name, is_active=True)
                except Course.DoesNotExist:
                    result.add_error(row_num, f"Course '{course_name}' not found")
                    result.skipped_count += 1
                    continue
                
                # Look up batch
                try:
                    batch = Batch.objects.get(batch_name=batch_name, is_active=True)
                except Batch.DoesNotExist:
                    result.add_error(row_num, f"Batch '{batch_name}' not found")
                    result.skipped_count += 1
                    continue
                
                # Create StudentMaster (derived fields auto-populate in save())
                StudentMaster.objects.create(
                    prn=prn,
                    student_full_name=student_full_name,
                    centre=centre,
                    course=course,
                    batch=batch,
                    is_active=True
                )
                
                result.created_count += 1
            
            except Exception as e:
                result.add_error(row_num, str(e))
                result.skipped_count += 1
    
    return result.to_dict()


# ==================== HORIZONTAL MARKS BULK UPLOAD ====================

def handle_horizontal_marks_bulk_upload(excel_file):
    """
    Upload marks into horizontally partitioned tables (ScoreCC, ScoreAP, etc.)
    Uses TestMapping to translate column headers to physical database slots.
    
    Expected Excel Format (Matrix):
    - prn
    - category_code
    - batch_name
    - Logical Name 1 (e.g. 'Math Quiz')
    - Logical Name 2 (e.g. 'Science Lab')
    ...
    """
    from apps.assessments.models import CATEGORY_SCORE_MODEL_MAP, TestMapping
    
    result = BulkUploadError()
    
    # Define flexible mapping
    possible_sheets = ['HorizontalMarks', 'MarksMatrix', 'CategoryScores', 'Marks']
    required_mapping = {
        'prn': ['student_prn', 'id'],
        'category_code': ['category', 'cat_code'],
        'batch_name': ['batch', 'batch_id']
    }
    
    try:
        # We read with no optional mapping first to get the basic info
        df = read_excel_flexible(excel_file, possible_sheets, required_mapping)
        # Note: read_excel_flexible only keeps the mapped columns. 
        # We actually need the FULL dataframe to get the score columns.
        original_df = pd.read_excel(excel_file, sheet_name=df.index.name if df.index.name else 0, keep_default_na=False) # Fallback to first sheet
        # Wait, read_excel_flexible should be improved or we do it manually here.
    except Exception as e:
        raise ValidationError(f"Excel parsing error: {str(e)}")

    # Re-read fully to get all headers
    xls = pd.ExcelFile(excel_file)
    sheet_name = None
    for s in possible_sheets:
        if s in xls.sheet_names:
            sheet_name = s
            break
    if not sheet_name: sheet_name = xls.sheet_names[0]
    
    full_df = pd.read_excel(excel_file, sheet_name=sheet_name, keep_default_na=False)
    
    with transaction.atomic():
        for idx, row in full_df.iterrows():
            row_num = idx + 2
            
            try:
                # 1. Basic info (try to find columns flexibly)
                norm_row = {str(k).lower().strip().replace(' ', '_'): v for k, v in row.items()}
                
                prn = None
                for alt in ['prn', 'student_prn', 'id']:
                    if alt in norm_row: 
                        prn = str(norm_row[alt]).strip()
                        break
                
                cat_code = None
                for alt in ['category_code', 'category', 'cat_code']:
                    if alt in norm_row:
                        cat_code = str(norm_row[alt]).strip()
                        break
                
                batch_name = None
                for alt in ['batch_name', 'batch', 'batch_id']:
                    if alt in norm_row:
                        batch_name = str(norm_row[alt]).strip()
                        break

                if not prn or not cat_code or not batch_name:
                    result.add_error(row_num, "Missing required columns: prn, category_code, or batch_name")
                    result.skipped_count += 1
                    continue

                # 2. Get student and their centre
                try:
                    student = StudentMaster.objects.get(prn=prn, is_active=True)
                except StudentMaster.DoesNotExist:
                    result.add_error(row_num, f"Student PRN '{prn}' not found")
                    result.skipped_count += 1
                    continue

                # 3. Get Model and Mappings
                if cat_code not in CATEGORY_SCORE_MODEL_MAP:
                    result.add_error(row_num, f"Invalid category code: '{cat_code}'")
                    result.skipped_count += 1
                    continue
                
                ModelClass = CATEGORY_SCORE_MODEL_MAP[cat_code]
                mappings = TestMapping.objects.filter(
                    batch_name=batch_name,
                    category_code=cat_code,
                    is_active=True
                )
                
                if not mappings.exists():
                    result.add_error(row_num, f"No TestMappings found for {batch_name}/{cat_code}")
                    result.skipped_count += 1
                    continue

                # 4. Process score columns
                score_data = {}
                # Normalize row headers: lowercase, stripped, and remove spaces for resilient matching
                import re
                row_headers = {str(k).strip().lower().replace(' ', ''): k for k in row.keys()}
                
                # Build fallback map of trailing numbers in column headers (e.g. 'aptest1' -> 1)
                header_seq_map = {}
                for clean_h, orig_h in row_headers.items():
                    m = re.search(r'\d+$', clean_h)
                    if m:
                        header_seq_map[int(m.group())] = orig_h
                
                for tm in mappings:
                    matched_header = None
                    logical_name = tm.logical_name.strip().lower().replace(' ', '')
                    
                    # Attempt 1: Exact match ignoring spaces
                    if logical_name in row_headers:
                        matched_header = row_headers[logical_name]
                    # Attempt 2: Fallback to matching by sequence number at the end of the column
                    elif tm.sequence in header_seq_map:
                        matched_header = header_seq_map[tm.sequence]
                        
                    if matched_header:
                        raw_val = row[matched_header]
                        if pd.notna(raw_val):
                            try:
                                # Handle numeric values and strings
                                score_val = Decimal(str(raw_val))
                                if score_val > tm.max_marks:
                                    result.add_warning(row_num, f"Score {score_val} for '{tm.logical_name}' exceeds max {tm.max_marks}")
                                score_data[tm.column_slot] = score_val
                            except Exception as e:
                                result.add_warning(row_num, f"Invalid score '{raw_val}' for '{tm.logical_name}'")
                        else:
                            score_data[tm.column_slot] = None

                if not score_data:
                    result.add_warning(row_num, "No matching test columns found for this row")
                    result.skipped_count += 1
                    continue

                # 5. Save to database
                score_obj, created = ModelClass.objects.update_or_create(
                    prn=student,
                    defaults=score_data
                )
                
                result.created_count += 1
            
            except Exception as e:
                result.add_error(row_num, str(e))
                result.skipped_count += 1
                
    return result.to_dict()

def handle_test_mapping_bulk_upload(excel_file):
    """
    Bulk upload TestMapping records
    """
    result = BulkUploadError()
    
    # Try mapping columns
    mapping = {
        'batch_name': ['batch', 'batchname', 'batch_id'],
        'category_code': ['category', 'categorycode'],
        'logical_name': ['test_name', 'subtest_name', 'name'],
        'column_slot': ['slot', 'column'],
        'max_marks': ['max_score', 'total_marks'],
        'sequence': ['order', 'seq']
    }
    
    df = read_excel_flexible(excel_file, ['TestMapping', 'TestMappings', 'SubTests', 'Sheet1'], mapping)
    
    # Cache limits
    category_limits = {}
    
    with transaction.atomic():
        for index, row in df.iterrows():
            row_num = index + 2
            try:
                # 1. Extract values
                batch_name = normalize_batch_name(row['batch_name'])
                category_code = str(row['category_code']).strip()
                logical_name = str(row['logical_name']).strip()
                column_slot = str(row['column_slot']).strip().lower()
                
                try:
                    max_marks = Decimal(str(row['max_marks']))
                except:
                    result.add_error(row_num, f"Invalid max_marks: {row['max_marks']}")
                    result.skipped_count += 1
                    continue
                    
                try:
                    sequence = int(row['sequence'])
                except:
                    sequence = 1
                
                # 2. Validate format
                if not column_slot.startswith('test_'):
                    result.add_error(row_num, f"column_slot must start with 'test_', got '{column_slot}'")
                    result.skipped_count += 1
                    continue
                    
                # 3. Check Category
                if category_code not in category_limits:
                    cat = MainCategory.objects.filter(category_code=category_code).first()
                    if not cat:
                        result.add_error(row_num, f"Invalid category_code: {category_code}")
                        result.skipped_count += 1
                        continue
                    category_limits[category_code] = cat
                
                category_obj = category_limits[category_code]
                
                # 4. Check limits (only if it's a new record we might exceed)
                existing = TestMapping.objects.filter(
                    batch_name_id=batch_name,
                    category_code=category_obj,
                    column_slot=column_slot
                ).first()
                
                if not existing:
                    # Creating new, check limit
                    current_count = TestMapping.objects.filter(
                        batch_name_id=batch_name,
                        category_code=category_obj,
                        is_active=True
                    ).count()
                    
                    if current_count >= category_obj.no_of_subtests:
                        result.add_error(row_num, f"Limit reached: Category {category_code} allows max {category_obj.no_of_subtests} subtests.")
                        result.skipped_count += 1
                        continue
                
                # 5. Create or Update
                TestMapping.objects.update_or_create(
                    batch_name_id=batch_name,
                    category_code=category_obj,
                    column_slot=column_slot,
                    defaults={
                        'logical_name': logical_name,
                        'max_marks': max_marks,
                        'sequence': sequence,
                        'is_active': True
                    }
                )
                result.created_count += 1
                
            except Exception as e:
                result.add_error(row_num, str(e))
                result.skipped_count += 1
                
    return result.to_dict()
