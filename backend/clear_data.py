#!/usr/bin/env python
"""
clear_data.py - Clear data from database while preserving schema

This script selectively clears data from tables:
- Clears student records
- Clears test records  
- Clears score records
- Optionally preserves lookup tables
- Creates backup before clearing
- Shows record counts before/after

Usage:
    python clear_data.py                    # Clear data only (preserve lookups)
    python clear_data.py --all              # Clear all data including lookups
    python clear_data.py --backup           # Create backup before clearing
    python clear_data.py --dry-run          # Show what would be deleted without deleting
"""

import os
import sys
import django
import json
from datetime import datetime
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev_settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.db import connection
from django.core.management import call_command
from apps.assessments.models import (
    StudentMaster, SubTest, StudentTestScore, ExamSchedule,
    Centre, Course, Batch, MainCategory, GradeScale
)


class DataCleaner:
    """Manages clearing data from database"""

    def __init__(self, dry_run=False, backup=False, clear_all=False):
        self.dry_run = dry_run
        self.backup = backup
        self.clear_all = clear_all
        self.backup_file = None
        self.stats = {
            'deleted': {},
            'preserved': {},
            'backup': None
        }

    def create_backup(self):
        """Create backup of database"""
        if not self.backup and not self.dry_run:
            return
            
        print("\n📦 Creating backup...")
        
        backup_dir = Path(__file__).parent / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_file = backup_dir / f'backup_{timestamp}.json'
        
        try:
            with open(self.backup_file, 'w') as f:
                call_command('dumpdata', 'assessments', stdout=f)
            print(f"✅ Backup created: {self.backup_file}")
            self.stats['backup'] = str(self.backup_file)
        except Exception as e:
            print(f"⚠️  Backup failed: {e}")

    def get_counts_before(self):
        """Get record counts before clearing"""
        print("\n📊 Record counts BEFORE clearing:")
        print("  Student data:")
        print(f"    • StudentMaster: {StudentMaster.objects.count()} records")
        print(f"    • SubTest: {SubTest.objects.count()} records")
        print(f"    • StudentTestScore: {StudentTestScore.objects.count()} records")
        print(f"    • ExamSchedule: {ExamSchedule.objects.count()} records")
        
        if self.clear_all:
            print("  Lookup data:")
            print(f"    • Centre: {Centre.objects.count()} records")
            print(f"    • Course: {Course.objects.count()} records")
            print(f"    • Batch: {Batch.objects.count()} records")
            print(f"    • MainCategory: {MainCategory.objects.count()} records")
            print(f"    • GradeScale: {GradeScale.objects.count()} records")

    def clear_data(self):
        """Clear data from database"""
        print("\n🗑️  Clearing data...")
        
        models_to_clear = [
            (StudentTestScore, "StudentTestScore"),
            (ExamSchedule, "ExamSchedule"),
            (SubTest, "SubTest"),
            (StudentMaster, "StudentMaster"),
        ]
        
        if self.clear_all:
            models_to_clear.extend([
                (Batch, "Batch"),
                (MainCategory, "MainCategory"),
                (Course, "Course"),
                (Centre, "Centre"),
                (GradeScale, "GradeScale"),
            ])
        
        for model, name in models_to_clear:
            count = model.objects.count()
            if count > 0:
                if self.dry_run:
                    print(f"  [DRY RUN] Would delete {count} {name} records")
                    self.stats['deleted'][name] = count
                else:
                    model.objects.all().delete()
                    print(f"  ✅ Deleted {count} {name} records")
                    self.stats['deleted'][name] = count
            else:
                print(f"  • {name}: Already empty")
                self.stats['deleted'][name] = 0

    def preserve_lookups(self):
        """Show preserved lookup data"""
        if self.clear_all:
            return
            
        print("\n📌 Preserved lookup data:")
        try:
            centres = Centre.objects.count()
            courses = Course.objects.count()
            batches = Batch.objects.count()
            categories = MainCategory.objects.count()
            grades = GradeScale.objects.count()
            
            print(f"  • Centre: {centres} records")
            print(f"  • Course: {courses} records")
            print(f"  • Batch: {batches} records")
            print(f"  • MainCategory: {categories} records")
            print(f"  • GradeScale: {grades} records")
            
            self.stats['preserved'] = {
                'Centre': centres,
                'Course': courses,
                'Batch': batches,
                'MainCategory': categories,
                'GradeScale': grades,
            }
        except Exception as e:
            print(f"⚠️  Error reading lookup data: {e}")

    def get_counts_after(self):
        """Get record counts after clearing"""
        print("\n📊 Record counts AFTER clearing:")
        print("  Student data:")
        print(f"    • StudentMaster: {StudentMaster.objects.count()} records")
        print(f"    • SubTest: {SubTest.objects.count()} records")
        print(f"    • StudentTestScore: {StudentTestScore.objects.count()} records")
        print(f"    • ExamSchedule: {ExamSchedule.objects.count()} records")
        
        if self.clear_all:
            print("  Lookup data:")
            print(f"    • Centre: {Centre.objects.count()} records")
            print(f"    • Course: {Course.objects.count()} records")
            print(f"    • Batch: {Batch.objects.count()} records")
            print(f"    • MainCategory: {MainCategory.objects.count()} records")
            print(f"    • GradeScale: {GradeScale.objects.count()} records")

    def save_stats(self):
        """Save stats to file"""
        stats_file = Path(__file__).parent / 'logs' / f'clear_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        stats_file.parent.mkdir(exist_ok=True)
        
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2, default=str)
        
        return stats_file

    def run(self):
        """Run the data clearing process"""
        print("=" * 60)
        print("DATA CLEANER - Phase 5")
        print("=" * 60)
        
        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No data will be deleted")
        
        self.get_counts_before()
        
        if not self.dry_run:
            if self.backup:
                self.create_backup()
            
            # Confirm before clearing
            if not self.clear_all:
                response = input("\n⚠️  This will clear student data. Continue? (yes/no): ")
            else:
                response = input("\n⚠️  This will clear ALL data including lookups. Continue? (yes/no): ")
            
            if response.lower() != 'yes':
                print("❌ Cancelled by user")
                return False
        
        self.clear_data()
        self.preserve_lookups()
        self.get_counts_after()
        
        if not self.dry_run:
            stats_file = self.save_stats()
            print(f"\n📝 Stats saved to: {stats_file}")
        
        print("\n" + "=" * 60)
        if self.dry_run:
            print("✅ Dry run completed successfully")
        else:
            print("✅ Data clearing completed successfully")
        print("=" * 60)
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Clear data from Student Dashboard database'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Clear all data including lookup tables'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create backup before clearing'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without deleting'
    )
    
    args = parser.parse_args()
    
    cleaner = DataCleaner(
        dry_run=args.dry_run,
        backup=args.backup,
        clear_all=args.all
    )
    
    success = cleaner.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
