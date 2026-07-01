"""
Seed script for Batch data
Creates sample batches
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev_settings')
django.setup()

from apps.assessments.models import Batch


def seed_batches():
    """Seed sample batches"""
    batches = [
        {
            'batch_name': 'Feb/24',
            'batch_month': '02',
            'batch_year': 2024,
            'is_active': True
        },
        {
            'batch_name': 'Aug/24',
            'batch_month': '08',
            'batch_year': 2024,
            'is_active': True
        },
        {
            'batch_name': 'Feb/25',
            'batch_month': '02',
            'batch_year': 2025,
            'is_active': True
        },
        {
            'batch_name': 'Aug/25',
            'batch_month': '08',
            'batch_year': 2025,
            'is_active': True
        },
        {
            'batch_name': 'Feb/23',
            'batch_month': '02',
            'batch_year': 2023,
            'is_active': True
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for batch_data in batches:
        try:
            batch, created = Batch.objects.get_or_create(
                batch_name=batch_data['batch_name'],
                defaults={
                    'batch_month': batch_data['batch_month'],
                    'batch_year': batch_data['batch_year'],
                    'is_active': batch_data['is_active']
                }
            )
            if created:
                print(f"✓ Created batch: {batch.batch_name}")
                created_count += 1
            else:
                print(f"⊘ Skipped (exists): {batch.batch_name}")
                skipped_count += 1
        except Exception as e:
            print(f"✗ Error creating batch {batch_data['batch_name']}: {str(e)}")
    
    print(f"\nSummary:")
    print(f"  Created: {created_count}")
    print(f"  Skipped: {skipped_count}")
    return created_count, skipped_count


if __name__ == '__main__':
    print("Seeding batches...")
    seed_batches()
    print("Batches seeding complete!")
