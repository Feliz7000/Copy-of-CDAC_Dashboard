"""
Migration 0007: Remove centre_code from TestMapping (single-centre system)

DB changes:
  1. Drop the old unique constraint (centre_code, batch_name, category_code, column_slot)
  2. Drop column centre_code from test_mapping
  3. Add unique constraint (batch_name, category_code, column_slot)
  4. Add unique constraint (batch_name, category_code, logical_name)

State changes:
  - Rebuild TestMapping model in Django state without centre_code field
  - Replace unique_together with two UniqueConstraints
  - Update indexes
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0006_align_db_with_reformed_models'),
    ]

    operations = [
        # ─── Step 1: Drop the old unique constraint (DB operation only) ───────
        # The old constraint is named based on Django's unique_together convention.
        # We do this first before dropping the column it references.
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        DO $$
                        DECLARE
                            constraint_name TEXT;
                        BEGIN
                            -- Find and drop any unique constraint involving centre_code on test_mapping
                            SELECT tc.constraint_name INTO constraint_name
                            FROM information_schema.table_constraints tc
                            JOIN information_schema.constraint_column_usage ccu
                              ON tc.constraint_name = ccu.constraint_name
                            WHERE tc.table_name = 'test_mapping'
                              AND tc.constraint_type = 'UNIQUE'
                              AND ccu.column_name = 'centre_code'
                            LIMIT 1;

                            IF constraint_name IS NOT NULL THEN
                                EXECUTE 'ALTER TABLE test_mapping DROP CONSTRAINT ' || quote_ident(constraint_name);
                            END IF;
                        END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[],
        ),

        # ─── Step 2: Drop the centre_code column from test_mapping ────────────
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        DO $$
                        BEGIN
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name = 'test_mapping'
                                  AND column_name = 'centre_code'
                            ) THEN
                                ALTER TABLE test_mapping DROP COLUMN centre_code;
                            END IF;
                        END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                # Rebuild TestMapping in Django's state without centre_code
                migrations.DeleteModel(name='TestMapping'),
                migrations.CreateModel(
                    name='TestMapping',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('batch_name', models.ForeignKey(
                            db_column='batch_name',
                            on_delete=django.db.models.deletion.PROTECT,
                            to='assessments.batch',
                            to_field='batch_name',
                        )),
                        ('category_code', models.ForeignKey(
                            db_column='category_code',
                            on_delete=django.db.models.deletion.PROTECT,
                            to='assessments.maincategory',
                            to_field='category_code',
                        )),
                        ('logical_name', models.CharField(max_length=100)),
                        ('column_slot', models.CharField(max_length=50)),
                        ('max_marks', models.DecimalField(decimal_places=2, max_digits=8)),
                        ('sequence', models.SmallIntegerField(default=1)),
                        ('is_active', models.BooleanField(default=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                        ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                    ],
                    options={
                        'verbose_name': 'Test Mapping',
                        'verbose_name_plural': 'Test Mappings',
                        'db_table': 'test_mapping',
                        'managed': True,
                    },
                ),
            ],
        ),

        # ─── Step 2.5: Remove duplicates before applying constraints ──────────
        migrations.RunSQL(
            sql="""
                -- Keep only the first occurrence for each batch_name, category_code, column_slot
                DELETE FROM test_mapping
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM test_mapping
                    GROUP BY batch_name, category_code, column_slot
                );

                -- Keep only the first occurrence for each batch_name, category_code, logical_name
                DELETE FROM test_mapping
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM test_mapping
                    GROUP BY batch_name, category_code, logical_name
                );
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # ─── Step 3: Add new unique constraints ───────────────────────────────
        migrations.AddConstraint(
            model_name='testmapping',
            constraint=models.UniqueConstraint(
                fields=['batch_name', 'category_code', 'column_slot'],
                name='uq_tm_batch_category_slot',
            ),
        ),
        migrations.AddConstraint(
            model_name='testmapping',
            constraint=models.UniqueConstraint(
                fields=['batch_name', 'category_code', 'logical_name'],
                name='uq_tm_batch_category_name',
            ),
        ),

        # ─── Step 4: Add optimised indexes ────────────────────────────────────
        migrations.AddIndex(
            model_name='testmapping',
            index=models.Index(fields=['batch_name', 'category_code'], name='assessments_tm_batch_cat_idx'),
        ),
        migrations.AddIndex(
            model_name='testmapping',
            index=models.Index(fields=['is_active'], name='assessments_tm_is_active_idx'),
        ),
    ]
