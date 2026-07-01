"""
Migration 0013: Create missing scores_gac and scores_prj tables.

The ScoreGAC and ScorePRJ models already exist in models.py with
managed = False, but the physical tables were never created. The score
matrix endpoint queries these tables directly, so they must exist even
if they start empty.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0012_alter_scoreap_options_alter_scoreas_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS scores_gac (
                id           BIGSERIAL PRIMARY KEY,
                prn          VARCHAR(20) NOT NULL REFERENCES student_master(prn),
                test_01      NUMERIC(8, 2),
                test_02      NUMERIC(8, 2),
                test_03      NUMERIC(8, 2),
                test_04      NUMERIC(8, 2),
                test_05      NUMERIC(8, 2),
                last_updated TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS scores_gac_prn_idx ON scores_gac (prn);

            CREATE TABLE IF NOT EXISTS scores_prj (
                id           BIGSERIAL PRIMARY KEY,
                prn          VARCHAR(20) NOT NULL REFERENCES student_master(prn),
                test_01      NUMERIC(8, 2),
                last_updated TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS scores_prj_prn_idx ON scores_prj (prn);
            """,
            reverse_sql="""
            DROP TABLE IF EXISTS scores_prj;
            DROP TABLE IF EXISTS scores_gac;
            """,
        ),
    ]