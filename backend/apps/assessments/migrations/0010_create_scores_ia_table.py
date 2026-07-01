"""
Migration 0010: Create missing scores_ia table.

The ScoreIA model (db_table='scores_ia') exists in models.py but the physical
table was never created. All other score tables (scores_cc, scores_ap, etc.)
already exist. We use RunSQL since the model is managed=False.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0009_remove_studentmaster_denorm_fields'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS scores_ia (
                id           BIGSERIAL PRIMARY KEY,
                prn          VARCHAR(20) NOT NULL REFERENCES student_master(prn),
                test_01      NUMERIC(8, 2),
                test_02      NUMERIC(8, 2),
                test_03      NUMERIC(8, 2),
                test_04      NUMERIC(8, 2),
                test_05      NUMERIC(8, 2),
                test_06      NUMERIC(8, 2),
                test_07      NUMERIC(8, 2),
                test_08      NUMERIC(8, 2),
                last_updated TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS scores_ia_prn_idx ON scores_ia (prn);
            """,
            reverse_sql="DROP TABLE IF EXISTS scores_ia;",
        ),
    ]
