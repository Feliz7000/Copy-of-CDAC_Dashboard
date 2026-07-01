"""
Migration 0008: Create system_config table for SystemConfig model.

This creates a new managed table 'system_config' with:
  key   VARCHAR(50) PRIMARY KEY
  value VARCHAR(100) NOT NULL

This is a pure new-table creation; no SeparateDatabaseAndState needed.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0007_remove_centre_from_testmapping'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemConfig',
            fields=[
                ('key',   models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('value', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'System Config',
                'verbose_name_plural': 'System Config',
                'db_table': 'system_config',
                'managed': True,
            },
        ),
    ]
