import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev_settings')
django.setup()

from apps.assessments.models import MainCategory, Centre, Batch, TestMapping

def seed_test_mappings():
    print("Starting Test Mapping seeding...")
    
    # 1. Get scope (adjust these if your database has different codes)
    try:
        mumbai = Centre.objects.get(centre_code='001')
        feb_batch = Batch.objects.get(batch_name='Feb/24')
    except Exception as e:
        print(f"Error: Could not find Mumbai (001) or Feb/24 batch. Please ensure they exist. Error: {e}")
        return

    # 2. Seed Aptitude (AP) Mappings
    try:
        cat_ap = MainCategory.objects.get(category_code='AP')
        ap_tests = [
            ('test_01', 'Quantitative Aptitude', 100),
            ('test_02', 'Logical Reasoning', 50),
            ('test_03', 'Verbal Ability', 50),
            ('test_04', 'Technical MCQ', 100),
        ]
        
        for i, (slot, name, marks) in enumerate(ap_tests):
            TestMapping.objects.update_or_create(
                centre_code=mumbai,
                batch_name=feb_batch,
                category_code=cat_ap,
                column_slot=slot,
                defaults={
                    'logical_name': name,
                    'max_marks': marks,
                    'sequence': i + 1,
                    'is_active': True
                }
            )
        print("✓ Seeded 4 Aptitude Test Mappings")
    except MainCategory.DoesNotExist:
        print("! Category 'AP' (Aptitude) not found, skipping.")

    # 3. Seed Module Tests (MT) Mappings
    try:
        cat_mt = MainCategory.objects.get(category_code='MT')
        mt_tests = [
            ('test_01', 'UI/UX Basics', 40),
            ('test_02', 'Core Javascript', 60),
            ('test_03', 'React Framework', 100),
        ]
        
        for i, (slot, name, marks) in enumerate(mt_tests):
            TestMapping.objects.update_or_create(
                centre_code=mumbai,
                batch_name=feb_batch,
                category_code=cat_mt,
                column_slot=slot,
                defaults={
                    'logical_name': name,
                    'max_marks': marks,
                    'sequence': i + 1,
                    'is_active': True
                }
            )
        print("✓ Seeded 3 Module Test Mappings")
    except MainCategory.DoesNotExist:
        print("! Category 'MT' (Module Tests) not found, skipping.")

    print("\nSuccess! You can now view these in the 'Marks Management' tab by selecting Mumbai, Feb/24, and the Category.")

if __name__ == "__main__":
    seed_test_mappings()
