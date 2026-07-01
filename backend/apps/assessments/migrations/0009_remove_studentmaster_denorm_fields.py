"""
Migration 0009: Remove denormalized CharField fields from StudentMaster.

Columns dropped from student_master:
  - centre_code_denorm  (was StudentMaster.centre_code)
  - centre_name
  - course_code_denorm  (was StudentMaster.course_code)
  - course_name
  - batch_name_denorm   (was StudentMaster.batch_name)

Also drop the old indexes on those columns and rebuild indexes on
the FK columns (centre_id, course_id, batch_id) which already exist.

Uses SeparateDatabaseAndState throughout because:
  - The denorm columns may or may not exist in the live DB.
  - The FK columns (centre_id, course_id, batch_id) already exist in DB
    as the actual FK storage columns.
  - We never want to accidentally drop-and-recreate student_master.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('assessments', '0008_systemconfig'),
    ]

    operations = [
        # ─── Drop denormalized columns (safe if they don't exist) ────────────
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        DO $$
                        BEGIN
                            -- centre_code_denorm
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name = 'student_master'
                                  AND column_name = 'centre_code_denorm'
                            ) THEN
                                ALTER TABLE student_master DROP COLUMN centre_code_denorm;
                            END IF;

                            -- centre_name
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name = 'student_master'
                                  AND column_name = 'centre_name'
                            ) THEN
                                ALTER TABLE student_master DROP COLUMN centre_name;
                            END IF;

                            -- course_code_denorm
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name = 'student_master'
                                  AND column_name = 'course_code_denorm'
                            ) THEN
                                ALTER TABLE student_master DROP COLUMN course_code_denorm;
                            END IF;

                            -- course_name
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name = 'student_master'
                                  AND column_name = 'course_name'
                            ) THEN
                                ALTER TABLE student_master DROP COLUMN course_name;
                            END IF;

                            -- batch_name_denorm
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name = 'student_master'
                                  AND column_name = 'batch_name_denorm'
                            ) THEN
                                ALTER TABLE student_master DROP COLUMN batch_name_denorm;
                            END IF;
                        END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                # Remove the denorm CharField fields from Django's state.
                # The FK fields (centre_id, course_id, batch_id) are unchanged.
                migrations.RemoveField(model_name='studentmaster', name='centre_code'),
                migrations.RemoveField(model_name='studentmaster', name='centre_name'),
                migrations.RemoveField(model_name='studentmaster', name='course_code'),
                migrations.RemoveField(model_name='studentmaster', name='course_name'),
                migrations.RemoveField(model_name='studentmaster', name='batch_name'),
            ],
        ),

        # ─── Update indexes on student_master ────────────────────────────────
        # Old indexes referencing the denorm columns are now stale.
        # We add proper indexes on the FK columns. Django will handle
        # the old index names gracefully (they may not exist in every env).
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        CREATE INDEX IF NOT EXISTS idx_sm_centre_id
                            ON student_master (centre_id);
                        CREATE INDEX IF NOT EXISTS idx_sm_course_id
                            ON student_master (course_id);
                        CREATE INDEX IF NOT EXISTS idx_sm_batch_id
                            ON student_master (batch_id);
                    """,
                    reverse_sql="""
                        DROP INDEX IF EXISTS idx_sm_centre_id;
                        DROP INDEX IF EXISTS idx_sm_course_id;
                        DROP INDEX IF EXISTS idx_sm_batch_id;
                    """,
                ),
            ],
            state_operations=[
                migrations.AlterModelOptions(
                    name='studentmaster',
                    options={
                        'verbose_name': 'Student Master',
                        'verbose_name_plural': 'Student Masters',
                    },
                ),
            ],
        ),
    ]
