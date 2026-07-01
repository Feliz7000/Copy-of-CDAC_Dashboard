import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Drops and recreates the placement analytics views: v_placement_report, v_ccee_ia_modules'

    def handle(self, *args, **options):
        project_root = settings.BASE_DIR
        sql_file_path = os.path.join(project_root, 'POSTGRESQL_ANALYTICS_VIEWS.sql')

        self.stdout.write(f'Reading SQL from {sql_file_path}...')

        if not os.path.exists(sql_file_path):
            self.stderr.write(self.style.ERROR(f'SQL file not found at {sql_file_path}'))
            return

        with open(sql_file_path, 'r', encoding='utf-8') as f:
            full_sql = f.read()

        # Extract only the two NEW placement views (VIEW 5 and VIEW 6).
        # The rest of the file references legacy tables that no longer exist.
        view5_marker = '-- VIEW 5: v_placement_report'
        view6_marker = '-- VIEW 6: v_ccee_ia_modules'
        view7_marker = '-- VIEW 7: v_inference_failed_criteria'

        idx5 = full_sql.find(view5_marker)
        if idx5 == -1:
            self.stderr.write(self.style.ERROR(
                'Could not find "VIEW 5: v_placement_report" in SQL file.'
            ))
            return

        tail = full_sql[idx5:]
        idx6 = tail.find(view6_marker)
        idx7 = tail.find(view7_marker)

        if idx6 != -1:
            view5_block = tail[:idx6]
            if idx7 != -1:
                view6_block = tail[idx6:idx7]
            else:
                view6_block = tail[idx6:]
        else:
            view5_block = tail
            view6_block = None

        def get_create_sql(block):
            if block is None:
                return None
            idx = block.find('CREATE OR REPLACE VIEW')
            return block[idx:].strip() if idx != -1 else None

        view5_sql = get_create_sql(view5_block)
        view6_sql = get_create_sql(view6_block)

        if not view5_sql:
            self.stderr.write(self.style.ERROR(
                'CREATE OR REPLACE VIEW not found for v_placement_report'
            ))
            return

        self.stdout.write('Dropping existing views...')
        try:
            with connection.cursor() as cursor:
                cursor.execute('DROP VIEW IF EXISTS v_ccee_ia_modules CASCADE;')
                cursor.execute('DROP VIEW IF EXISTS v_placement_report CASCADE;')

                self.stdout.write('Creating v_placement_report...')
                cursor.execute(view5_sql)
                self.stdout.write(self.style.SUCCESS('[OK] v_placement_report created'))

                if view6_sql:
                    self.stdout.write('Creating v_ccee_ia_modules...')
                    cursor.execute(view6_sql)
                    self.stdout.write(self.style.SUCCESS('[OK] v_ccee_ia_modules created'))
                else:
                    self.stdout.write(self.style.WARNING('[WARN] v_ccee_ia_modules section not found - skipped'))

            self.stdout.write(self.style.SUCCESS('Placement analytics views created successfully.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {e}'))
            raise
