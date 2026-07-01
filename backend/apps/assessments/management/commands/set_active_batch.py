# File: backend/apps/assessments/management/commands/set_active_batch.py
"""
Management command: set_active_batch
Usage: python manage.py set_active_batch 'Feb/24'

Sets the system-wide active batch in the SystemConfig table.
Validates that the batch exists in the batches table before saving.
"""
from django.core.management.base import BaseCommand, CommandError
from apps.assessments.models import SystemConfig


class Command(BaseCommand):
    help = 'Set the currently active batch for the system'

    def add_arguments(self, parser):
        parser.add_argument(
            'batch_name',
            type=str,
            help="Batch name e.g. 'Feb/24' or 'Aug/24'"
        )

    def handle(self, *args, **options):
        batch_name = options['batch_name']
        try:
            SystemConfig.set_active_batch(batch_name)
            self.stdout.write(
                self.style.SUCCESS(f"Active batch set to '{batch_name}'")
            )
        except ValueError as e:
            raise CommandError(str(e))
