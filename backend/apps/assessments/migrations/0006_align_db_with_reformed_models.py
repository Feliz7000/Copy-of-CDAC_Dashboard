"""
Migration 0006: Align DB with reformed models.py

Changes (all already exist in DB — using SeparateDatabaseAndState to reconcile):
1. CategoryCourseMapping: remove old mapping_id PK + rename FK columns to category_code/course_code
   -> DB already has category_code and course_code columns
2. TestMapping: db_table rename test_mappings -> test_mapping
   -> DB already has table named test_mapping (singular)
3. Score models: rename db_table score_XX -> scores_XX and declare managed=False
   -> DB already has tables named scores_XX
4. BaseScoreModel: db_column aliases for SubTest_N -> test_NN and updated_at -> last_updated
   -> Pure Python-level aliases, no DB change needed

We use SeparateDatabaseAndState to update Django's migration state without
touching the DB (since the DB already has the correct structure).
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0005_alter_scoreap_prn_alter_scoreas_prn_and_more'),
    ]

    operations = [
        # ─────────────────────────────────────────────────────────
        # 1. CategoryCourseMapping: align Python model state with DB
        #    DB already has: category_code (FK→main_categories), course_code (FK→courses)
        #    Old state had: mapping_id PK, category_id (FK→maincategory), course_id (FK→course)
        # ─────────────────────────────────────────────────────────
        migrations.SeparateDatabaseAndState(
            database_operations=[],   # DB is already correct
            state_operations=[
                migrations.DeleteModel(name='CategoryCourseMapping'),
                migrations.CreateModel(
                    name='CategoryCourseMapping',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('category', models.ForeignKey(
                            db_column='category_code',
                            on_delete=django.db.models.deletion.CASCADE,
                            to='assessments.maincategory',
                            to_field='category_code',
                        )),
                        ('course', models.ForeignKey(
                            db_column='course_code',
                            on_delete=django.db.models.deletion.CASCADE,
                            to='assessments.course',
                            to_field='course_code',
                        )),
                        ('is_active', models.BooleanField(default=True)),
                    ],
                    options={
                        'db_table': 'category_course_mapping',
                        'managed': True,
                        'unique_together': {('category', 'course')},
                    },
                ),
            ],
        ),

        # ─────────────────────────────────────────────────────────
        # 2. TestMapping: reconcile db_table name (test_mapping singular)
        #    DB has: test_mapping (singular) with created_at, updated_at
        # ─────────────────────────────────────────────────────────
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterModelTable(
                    name='testmapping',
                    table='test_mapping',
                ),
            ],
        ),

        # ─────────────────────────────────────────────────────────
        # 3. Score models: reconcile db_table names + set managed=False
        #    DB has: scores_ap, scores_as, scores_cc, etc. with test_01..20 + last_updated
        # ─────────────────────────────────────────────────────────
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                # Delete old managed Score models
                migrations.DeleteModel(name='ScoreAP'),
                migrations.DeleteModel(name='ScoreAS'),
                migrations.DeleteModel(name='ScoreCC'),
                migrations.DeleteModel(name='ScoreGR'),
                migrations.DeleteModel(name='ScoreIN'),
                migrations.DeleteModel(name='ScoreMT'),
                migrations.DeleteModel(name='ScoreNA'),
                migrations.DeleteModel(name='ScorePQ'),
                migrations.DeleteModel(name='ScorePS'),
                migrations.DeleteModel(name='ScoreSX'),
                migrations.DeleteModel(name='ScoreTA'),
            ],
        ),
    ]
