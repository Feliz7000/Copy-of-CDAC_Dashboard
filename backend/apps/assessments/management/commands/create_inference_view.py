import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Drops and recreates v_inference_failed_criteria'

    def handle(self, *args, **options):
        project_root = settings.BASE_DIR
        sql_file_path = os.path.join(project_root, 'POSTGRESQL_ANALYTICS_VIEWS.sql')

        self.stdout.write(f'Reading SQL from {sql_file_path}...')

        if not os.path.exists(sql_file_path):
            self.stderr.write(self.style.ERROR(f'SQL file not found at {sql_file_path}'))
            return

        with open(sql_file_path, 'r', encoding='utf-8') as f:
            full_sql = f.read()

        view7_marker = '-- VIEW 7: v_inference_failed_criteria'
        idx7 = full_sql.find(view7_marker)

        if idx7 == -1:
            self.stderr.write(self.style.ERROR(
                'Could not find "VIEW 7: v_inference_failed_criteria" in SQL file.'
            ))
            return

        view7_block = full_sql[idx7:]
        create_idx = view7_block.find('CREATE OR REPLACE VIEW')
        view7_sql = view7_block[create_idx:].strip() if create_idx != -1 else None

        if not view7_sql:
            self.stderr.write(self.style.ERROR(
                'CREATE OR REPLACE VIEW not found for v_inference_failed_criteria'
            ))
            return

        self.stdout.write('Dropping existing view...')
        try:
            with connection.cursor() as cursor:
                cursor.execute('DROP VIEW IF EXISTS v_inference_failed_criteria CASCADE;')

                self.stdout.write('Creating v_inference_failed_criteria...')
                cursor.execute(view7_sql)
                self.stdout.write(self.style.SUCCESS('[OK] v_inference_failed_criteria created'))

            self.stdout.write(self.style.SUCCESS('Inference view created successfully.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {e}'))
            raise