#!/usr/bin/env python
"""
reset_database.py - Complete database reset

This script performs a complete database reset:
- Creates backup of existing data
- Drops all tables
- Runs fresh migrations
- Seeds lookup tables
- Verifies clean state
- Generates reset report

Usage:
    python reset_database.py              # Full reset with confirmation
    python reset_database.py --no-seed    # Reset without seeding
    python reset_database.py --no-backup  # Reset without backup
    python reset_database.py --yes        # Reset without confirmation
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
from django.core.management.sql import emit_post_migrate_signal
from apps.assessments.models import (
    StudentMaster, SubTest, StudentTestScore, ExamSchedule,
    Centre, Course, Batch, MainCategory, GradeScale
)


class DatabaseResetter:
    """Manages complete database reset"""

    def __init__(self, backup=True, seed=True, confirm=True):
        self.backup = backup
        self.seed = seed
        self.confirm = confirm
        self.backup_file = None
        self.stats = {
            'timestamp': datetime.now().isoformat(),
            'backup': None,
            'migration_status': None,
            'seed_status': None,
            'final_counts': {}
        }

    def create_backup(self):
        """Create backup of database before reset"""
        if not self.backup:
            return True
            
        print("\n📦 Creating backup...")
        
        backup_dir = Path(__file__).parent / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_file = backup_dir / f'backup_before_reset_{timestamp}.json'
        
        try:
            with open(self.backup_file, 'w') as f:
                call_command('dumpdata', 'assessments', stdout=f)
            print(f"✅ Backup created: {self.backup_file}")
            self.stats['backup'] = str(self.backup_file)
            return True
        except Exception as e:
            print(f"⚠️  Backup failed: {e}")
            response = input("Continue without backup? (yes/no): ")
            if response.lower() != 'yes':
                return False
            self.stats['backup'] = f"Failed: {str(e)}"
            return True

    def drop_all_data(self):
        """Drop all data from database"""
        print("\n🗑️  Dropping all tables...")
        
        try:
            with connection.cursor() as cursor:
                # Get database engine type
                db_engine = connection.settings_dict['ENGINE']
                
                if 'sqlite' in db_engine:
                    # SQLite: Drop all tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    for table in tables:
                        if table[0] not in ['sqlite_sequence']:
                            cursor.execute(f'DROP TABLE IF EXISTS "{table[0]}"')
                    print(f"✅ Dropped {len(tables)} tables")
                    
                elif 'mysql' in db_engine:
                    # MySQL: Drop all tables
                    cursor.execute("SHOW TABLES;")
                    tables = cursor.fetchall()
                    cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
                    for table in tables:
                        cursor.execute(f'DROP TABLE IF EXISTS `{table[0]}`')
                    cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
                    print(f"✅ Dropped {len(tables)} tables")
                    
                elif 'postgresql' in db_engine:
                    # PostgreSQL: Drop all tables
                    cursor.execute("""
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname NOT IN ('pg_catalog', 'information_schema');
                    """)
                    tables = cursor.fetchall()
                    for table in tables:
                        cursor.execute(f'DROP TABLE IF EXISTS "{table[0]}" CASCADE')
                    print(f"✅ Dropped {len(tables)} tables")
                    
            return True
        except Exception as e:
            print(f"❌ Error dropping tables: {e}")
            return False

    def run_migrations(self):
        """Run Django migrations"""
        print("\n🔧 Running migrations...")
        
        try:
            call_command('migrate', verbosity=1)
            print("✅ Migrations completed")
            self.stats['migration_status'] = 'success'
            return True
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            self.stats['migration_status'] = f"failed: {str(e)}"
            return False

    def seed_lookups(self):
        """Seed lookup tables"""
        if not self.seed:
            print("\n⏭️  Skipping seed data (use --seed to enable)")
            return True
            
        print("\n🌱 Seeding lookup tables...")
        
        try:
            # Import seed scripts
            from seed_centres import seed_centres
            from seed_courses import seed_courses
            from seed_batches import seed_batches
            from seed_categories import seed_categories
            from seed_grade_scale import seed_grade_scale
            
            results = []
            
            # Seed each table
            result = seed_centres()
            results.append(('Centre', result))
            
            result = seed_courses()
            results.append(('Course', result))
            
            result = seed_batches()
            results.append(('Batch', result))
            
            result = seed_categories()
            results.append(('MainCategory', result))
            
            result = seed_grade_scale()
            results.append(('GradeScale', result))
            
            # Print results
            total_created = 0
            for name, count in results:
                print(f"  ✅ {name}: {count} records created")
                total_created += count
            
            print(f"📊 Total: {total_created} records seeded")
            self.stats['seed_status'] = 'success'
            return True
            
        except Exception as e:
            print(f"❌ Seeding failed: {e}")
            self.stats['seed_status'] = f"failed: {str(e)}"
            return False

    def verify_tables(self):
        """Verify tables were created correctly"""
        print("\n✅ Verifying database structure...")
        
        try:
            # Check table exists and has correct fields
            with connection.cursor() as cursor:
                db_engine = connection.settings_dict['ENGINE']
                
                if 'sqlite' in db_engine:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = [row[0] for row in cursor.fetchall()]
                elif 'mysql' in db_engine:
                    cursor.execute("SHOW TABLES;")
                    tables = [row[0] for row in cursor.fetchall()]
                else:  # PostgreSQL
                    cursor.execute("""
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname = 'public';
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
                
                print(f"  ✅ Tables created: {len(tables)}")
                for table in sorted(tables):
                    print(f"    • {table}")
                
            return True
        except Exception as e:
            print(f"⚠️  Verification warning: {e}")
            return True

    def get_final_counts(self):
        """Get final record counts"""
        print("\n📊 Final record counts:")
        
        try:
            counts = {
                'Centre': Centre.objects.count(),
                'Course': Course.objects.count(),
                'Batch': Batch.objects.count(),
                'MainCategory': MainCategory.objects.count(),
                'GradeScale': GradeScale.objects.count(),
                'StudentMaster': StudentMaster.objects.count(),
                'SubTest': SubTest.objects.count(),
                'StudentTestScore': StudentTestScore.objects.count(),
                'ExamSchedule': ExamSchedule.objects.count(),
            }
            
            for name, count in counts.items():
                print(f"  • {name}: {count} records")
            
            self.stats['final_counts'] = counts
        except Exception as e:
            print(f"⚠️  Error getting counts: {e}")

    def save_report(self):
        """Save reset report"""
        report_dir = Path(__file__).parent / 'reports'
        report_dir.mkdir(exist_ok=True)
        
        report_file = report_dir / f'reset_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(report_file, 'w') as f:
            json.dump(self.stats, f, indent=2, default=str)
        
        print(f"\n📝 Report saved: {report_file}")
        return report_file

    def run(self):
        """Run the complete reset process"""
        print("=" * 60)
        print("DATABASE RESET - Phase 5")
        print("=" * 60)
        
        if self.confirm:
            print("\n⚠️  This will COMPLETELY reset the database:")
            print("  • All tables will be dropped")
            print("  • All data will be deleted")
            print("  • Database will be rebuilt from scratch")
            if self.backup:
                print("  • Backup will be created first")
            
            response = input("\nContinue? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Reset cancelled")
                return False
        
        # Execute reset steps
        if not self.create_backup():
            return False
        
        if not self.drop_all_data():
            return False
        
        if not self.run_migrations():
            return False
        
        if not self.seed_lookups():
            return False
        
        if not self.verify_tables():
            return False
        
        self.get_final_counts()
        self.save_report()
        
        print("\n" + "=" * 60)
        print("✅ Database reset completed successfully!")
        print("=" * 60)
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Complete database reset for Student Dashboard'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip backup creation'
    )
    parser.add_argument(
        '--no-seed',
        action='store_true',
        help='Skip seeding lookup tables'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Skip confirmation prompt'
    )
    
    args = parser.parse_args()
    
    resetter = DatabaseResetter(
        backup=not args.no_backup,
        seed=not args.no_seed,
        confirm=not args.yes
    )
    
    success = resetter.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
