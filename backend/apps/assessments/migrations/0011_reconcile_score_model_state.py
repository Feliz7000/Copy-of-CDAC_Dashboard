"""
Migration 0011: Reconcile Django migration state with the actual database.

All the DB changes here already exist (tables, indexes, FK columns).
We use SeparateDatabaseAndState so Django's state catches up without
touching the database. The score models (managed=False) were deleted
from state in 0006 but never re-added; we add them back now.
"""
import django.db.models.deletion
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0010_create_scores_ia_table'),
    ]

    operations = [
        # ── Re-register all managed=False score models in state ────────────
        migrations.SeparateDatabaseAndState(
            database_operations=[],   # DB already has all these tables
            state_operations=[
                # ScoreAP
                migrations.CreateModel(
                    name='ScoreAP',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='last_updated')),
                        ('test_01', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_02', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_03', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_04', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_05', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_06', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_07', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_08', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_09', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_10', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_11', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_12', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_13', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_14', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_15', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_16', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_17', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_18', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_19', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('test_20', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('prn', models.ForeignKey(db_column='prn', on_delete=django.db.models.deletion.PROTECT, to='assessments.studentmaster')),
                    ],
                    options={'db_table': 'scores_ap', 'managed': False},
                ),
                # ScoreAS
                migrations.CreateModel(
                    name='ScoreAS',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='last_updated')),
                        *[(f'test_{i:02d}', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)) for i in range(1, 31)],
                        ('prn', models.ForeignKey(db_column='prn', on_delete=django.db.models.deletion.PROTECT, to='assessments.studentmaster')),
                    ],
                    options={'db_table': 'scores_as', 'managed': False},
                ),
                # ScoreCC
                migrations.CreateModel(
                    name='ScoreCC',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='last_updated')),
                        *[(f'test_{i:02d}', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)) for i in range(1, 9)],
                        ('prn', models.ForeignKey(db_column='prn', on_delete=django.db.models.deletion.PROTECT, to='assessments.studentmaster')),
                    ],
                    options={'db_table': 'scores_cc', 'managed': False},
                ),
                # ScoreGR
                migrations.CreateModel(
                    name='ScoreGR',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='last_updated')),
                        *[(f'test_{i:02d}', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)) for i in range(1, 11)],
                        ('prn', models.ForeignKey(db_column='prn', on_delete=django.db.models.deletion.PROTECT, to='assessments.studentmaster')),
                    ],
                    options={'db_table': 'scores_gr', 'managed': False},
                ),
                # ScoreIA
                migrations.CreateModel(
                    name='ScoreIA',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='last_updated')),
                        *[(f'test_{i:02d}', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)) for i in range(1, 9)],
                        ('prn', models.ForeignKey(db_column='prn', on_delete=django.db.models.deletion.PROTECT, to='assessments.studentmaster')),
                    ],
                    options={'db_table': 'scores_ia', 'managed': False},
                ),
                # ScoreIN
                migrations.CreateModel(
                    name='ScoreIN',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='last_updated')),
                        *[(f'test_{i:02d}', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)) for i in range(1, 6)],
                        ('prn', models.ForeignKey(db_column='prn', on_delete=django.db.models.deletion.PROTECT, to='assessments.studentmaster')),
                    ],
                    options={'db_table': 'scores_in', 'managed': False},
                ),
                # ScoreNA
                migrations.CreateModel(
                    name='ScoreNA',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='last_updated')),
                        *[(f'test_{i:02d}', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)) for i in range(1, 6)],
                        ('prn', models.ForeignKey(db_column='prn', on_delete=django.db.models.deletion.PROTECT, to='assessments.studentmaster')),
                    ],
                    options={'db_table': 'scores_na', 'managed': False},
                ),
                # ScorePQ
                migrations.CreateModel(
                    name='ScorePQ',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='last_updated')),
                        *[(f'test_{i:02d}', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)) for i in range(1, 31)],
                        ('prn', models.ForeignKey(db_column='prn', on_delete=django.db.models.deletion.PROTECT, to='assessments.studentmaster')),
                    ],
                    options={'db_table': 'scores_pq', 'managed': False},
                ),
                # ScorePS
                migrations.CreateModel(
                    name='ScorePS',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='last_updated')),
                        *[(f'test_{i:02d}', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)) for i in range(1, 11)],
                        ('prn', models.ForeignKey(db_column='prn', on_delete=django.db.models.deletion.PROTECT, to='assessments.studentmaster')),
                    ],
                    options={'db_table': 'scores_ps', 'managed': False},
                ),
                # ScoreSX
                migrations.CreateModel(
                    name='ScoreSX',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='last_updated')),
                        *[(f'test_{i:02d}', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)) for i in range(1, 11)],
                        ('prn', models.ForeignKey(db_column='prn', on_delete=django.db.models.deletion.PROTECT, to='assessments.studentmaster')),
                    ],
                    options={'db_table': 'scores_sx', 'managed': False},
                ),
                # ScoreTA
                migrations.CreateModel(
                    name='ScoreTA',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('updated_at', models.DateTimeField(auto_now=True, db_column='last_updated')),
                        *[(f'test_{i:02d}', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)) for i in range(1, 6)],
                        ('prn', models.ForeignKey(db_column='prn', on_delete=django.db.models.deletion.PROTECT, to='assessments.studentmaster')),
                    ],
                    options={'db_table': 'scores_ta', 'managed': False},
                ),
            ],
        ),

        # ── Reconcile StudentMaster index names (state-only) ───────────────
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterModelOptions(
                    name='studentmaster',
                    options={
                        'db_table': 'student_master',
                        'managed': True,
                        'verbose_name': 'Student Master',
                        'verbose_name_plural': 'Student Masters',
                    },
                ),
            ],
        ),
    ]
