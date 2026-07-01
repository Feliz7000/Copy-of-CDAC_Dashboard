# backend/seed_assessments.py
import os
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev_settings')
django.setup()

from apps.assessments.models import (
    MainCategory, Course, CategoryCourseMapping, 
    TestMapping, Centre, Batch
)

def seed():
    print("🚀 Starting Assessment Seeding...")
    
    # 1. Ensure course 20 exists
    course, _ = Course.objects.get_or_create(
        course_code='20', 
        defaults={'course_name': 'Advanced Computing Program', 'is_active': True}
    )
    print(f"✅ Course: {course.course_code}")

    # 2. Ensure Categories exist and map them to the course
    category_data = {
        'CC': 'Common Campus Component',
        'IA': 'IA / Module Test',
        'AP': 'Aptitude Assessment',
        'SX': 'Speak X (Communication)',
        'PS': 'Personality & Soft Skills',
        'GR': 'General Records',
        'TA': 'Technical Activity',
        'NA': 'Non-Technical Activity',
        'AS': 'Assignments',
        'PQ': 'Practice Quizzes',
        'IN': 'Interview Preparation',
        'GAC': 'GAC Grade',
        'PRJ': 'Project Grade'
    }

    for code, name in category_data.items():
        defaults = {
            'category_name': name,
            'no_of_subtests': 10,
            'max_marks_per_subtest': 100,
            'scaled_marks': 100.0,
            'is_active': True
        }
        if code == 'GAC':
            defaults.update({
                'no_of_subtests': 5,
                'max_marks_per_subtest': 40,
                'scaled_marks': 100.0,
            })
        elif code == 'PRJ':
            defaults.update({
                'no_of_subtests': 1,
                'max_marks_per_subtest': 100,
                'scaled_marks': 100.0,
            })

        cat, _ = MainCategory.objects.get_or_create(
            category_code=code,
            defaults=defaults
        )
        # Link to course
        CategoryCourseMapping.objects.get_or_create(category=cat, course=course)
    print(f"✅ Categories & Course Mappings: {len(category_data)} categories linked to course {course.course_code}")

    # 3. Seed TestMapping for Centre 403, Batch Aug/24
    centre, _ = Centre.objects.get_or_create(
        centre_code='403', 
        defaults={'centre_name': 'Mumbai', 'is_active': True}
    )
    batch, _ = Batch.objects.get_or_create(
        batch_name='Aug/24', 
        defaults={'batch_month': '08', 'batch_year': 2024, 'is_active': True}
    )
    print(f"✅ Scope: Centre {centre.centre_code}, Batch {batch.batch_name}")

    mappings = [
        # CC: 8 tests
        *[( 'CC', f'CCEE - M{i}', f'test_{i:02d}', 40.0, i) for i in range(1, 9)],
        # IA: 8 tests
        *[( 'IA', f'IA - M{i}', f'test_{i:02d}', 60.0 if i < 8 else 10.0, i) for i in range(1, 9)],
        # AP: 20 tests
        *[( 'AP', f'Aptitude Test {i}', f'test_{i:02d}', 10.0, i) for i in range(1, 21)],
        # SX: 10 tests
        *[( 'SX', f'Speak X Test {i}', f'test_{i:02d}', 10.0, i) for i in range(1, 11)],
        # PS: 10 tests (Behavioral)
        ('PS', 'Behavior', 'test_01', 10.0, 1), ('PS', 'Participation', 'test_02', 10.0, 2),
        ('PS', 'Attitude', 'test_03', 10.0, 3), ('PS', 'Communication', 'test_04', 10.0, 4),
        ('PS', 'Confidence', 'test_05', 10.0, 5), ('PS', 'Leadership', 'test_06', 10.0, 6),
        ('PS', 'Honesty', 'test_07', 10.0, 7), ('PS', 'Respect', 'test_08', 10.0, 8),
        ('PS', 'Creativity', 'test_09', 10.0, 9), ('PS', 'Resilience', 'test_10', 10.0, 10),
        # GR: 10 tests (General)
        ('GR', 'Attendance', 'test_01', 10.0, 1), ('GR', 'Punctuality', 'test_02', 10.0, 2),
        ('GR', 'Discipline', 'test_03', 10.0, 3), ('GR', 'Homework Completion', 'test_04', 10.0, 4),
        ('GR', 'Digital Literacy', 'test_05', 10.0, 5), ('GR', 'Responsibility', 'test_06', 10.0, 6),
        ('GR', 'Preparedness for Class', 'test_07', 10.0, 7), ('GR', 'Listening Skills', 'test_08', 10.0, 8),
        ('GR', 'Teamwork', 'test_09', 10.0, 9), ('GR', 'Professionalism', 'test_10', 10.0, 10),
        # Activities
        *[( 'TA', f'Technical Activity {i}', f'test_{i:02d}', 20.0, i) for i in range(1, 6)],
        *[( 'NA', f'Non-Technical Activity {i}', f'test_{i:02d}', 20.0, i) for i in range(1, 6)],
        # Assignments/Quizzes
        *[( 'AS', f'Assignment Test {i}', f'test_{i:02d}', 10.0, i) for i in range(1, 31)],
        *[( 'PQ', f'Practice Quiz {i}', f'test_{i:02d}', 10.0, i) for i in range(1, 31)],
        # GAC / Project
        ('GAC', 'CCEE Aptitude', 'test_01', 40.0, 1),
        ('GAC', 'Speak X Total', 'test_02', 60.0, 2),
        ('GAC', 'Aptitude Total', 'test_03', 40.0, 3),
        ('GAC', 'Introduction', 'test_04', 10.0, 4),
        ('GAC', 'GD', 'test_05', 10.0, 5),
        ('PRJ', 'Project Total', 'test_01', 100.0, 1),
        # Interview Mock
        ('IN', 'Interview Mock Test 1', 'test_01', 10.0, 1),
        ('IN', 'Interview Mock Test 2', 'test_02', 10.0, 2),
        ('IN', 'Interview Mock GD 1', 'test_03', 10.0, 3),
        ('IN', 'Interview Mock GD 2', 'test_04', 10.0, 4),
        ('IN', 'Team Interview', 'test_05', 10.0, 5),
    ]

    count = 0
    for cat_code, logical, slot, marks, seq in mappings:
        cat = MainCategory.objects.get(category_code=cat_code)
        TestMapping.objects.get_or_create(
            batch_name=batch,
            category_code=cat,
            column_slot=slot,
            defaults={
                'logical_name': logical,
                'max_marks': Decimal(str(marks)),
                'sequence': seq,
                'is_active': True
            }
        )
        count += 1
    
    print(f"✅ Test Mappings: Created/Verified {count} mappings.")
    print("\n✨ SEEDING COMPLETE!")

if __name__ == "__main__":
    seed()
