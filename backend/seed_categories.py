"""
Seed script for MainCategory data
Creates sample assessment categories
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev_settings')
django.setup()

from apps.assessments.models import MainCategory


def seed_categories():
    """Seed sample main categories"""
    categories = [
        {
            'category_code': 'GAC',
            'category_name': 'GAC Grade',
            'description': 'Composite GAC grading category',
            'max_marks_per_subtest': Decimal('40.00'),
            'no_of_subtests': 5,
            'scaled_marks': Decimal('100.00'),
            'is_active': True
        },
        {
            'category_code': 'PRJ',
            'category_name': 'Project Grade',
            'description': 'Project grading category',
            'max_marks_per_subtest': Decimal('100.00'),
            'no_of_subtests': 1,
            'scaled_marks': Decimal('100.00'),
            'is_active': True
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for category_data in categories:
        try:
            category, created = MainCategory.objects.get_or_create(
                category_code=category_data['category_code'],
                defaults={
                    'category_name': category_data['category_name'],
                    'description': category_data['description'],
                    'max_marks_per_subtest': category_data['max_marks_per_subtest'],
                    'no_of_subtests': category_data['no_of_subtests'],
                    'scaled_marks': category_data['scaled_marks'],
                    'is_active': category_data['is_active']
                }
            )
            if created:
                print(f"✓ Created category: {category.category_code} - {category.category_name}")
                created_count += 1
            else:
                print(f"⊘ Skipped (exists): {category.category_code} - {category.category_name}")
                skipped_count += 1
        except Exception as e:
            print(f"✗ Error creating category {category_data['category_code']}: {str(e)}")
    
    print(f"\nSummary:")
    print(f"  Created: {created_count}")
    print(f"  Skipped: {skipped_count}")
    return created_count, skipped_count


if __name__ == '__main__':
    print("Seeding categories...")
    seed_categories()
    print("Categories seeding complete!")
