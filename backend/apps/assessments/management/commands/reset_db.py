"""
Django management command: reset_db
Usage: python manage.py reset_db --confirm
Clears all data (sets is_active=False) for fresh start
"""
from django.core.management.base import BaseCommand
from apps.assessments.models import (
    Centre, Course, Batch, MainCategory, GradeScale,
    StudentMaster, SubTest, StudentTestScore, ExamSchedule
)


class Command(BaseCommand):
    help = 'Soft-delete all data (set is_active=False) for fresh start'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion (required for safety)'
        )
        parser.add_argument(
            '--hard',
            action='store_true',
            help='Permanently delete records (DANGEROUS!)'
        )
    
    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.ERROR(
                "✗ Safety check: Use --confirm flag to proceed"
            ))
            return
        
        self.stdout.write("=" * 70)
        self.stdout.write("RESETTING DATABASE")
        self.stdout.write("=" * 70)
        
        is_hard = options['hard']
        action = "PERMANENTLY DELETE" if is_hard else "Soft-delete (is_active=False)"
        
        self.stdout.write(f"\nAction: {action}")
        self.stdout.write("\nTables to reset:")
        
        tables = [
            ('StudentTestScore', StudentTestScore),
            ('ExamSchedule', ExamSchedule),
            ('SubTest', SubTest),
            ('StudentMaster', StudentMaster),
            ('MainCategory', MainCategory),
            ('Batch', Batch),
            ('Course', Course),
            ('Centre', Centre),
            ('GradeScale', GradeScale),
        ]
        
        total_deleted = 0
        
        for name, model in tables:
            # Count records
            count = model.objects.count()
            
            if count == 0:
                self.stdout.write(f"  ⊘ {name}: {count} records (nothing to delete)")
                continue
            
            if is_hard:
                # Hard delete
                deleted_count, _ = model.objects.all().delete()
                self.stdout.write(self.style.WARNING(f"  ✓ {name}: {deleted_count} records PERMANENTLY DELETED"))
                total_deleted += deleted_count
            else:
                # Soft delete
                if hasattr(model, '_meta') and any(
                    f.name == 'is_active' for f in model._meta.get_fields()
                ):
                    updated = model.objects.filter(is_active=True).update(is_active=False)
                    self.stdout.write(f"  ✓ {name}: {updated} records marked inactive")
                    total_deleted += updated
                else:
                    self.stdout.write(f"  ⊘ {name}: No is_active field (skipped)")
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(f"RESET COMPLETE: {total_deleted} records processed")
        self.stdout.write("=" * 70)
