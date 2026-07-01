from django.test import SimpleTestCase

from apps.assessments.report_views import _normalize_placement_status


class PlacementStatusNormalizationTests(SimpleTestCase):
    def test_sql_eligible_maps_to_placement_ready(self):
        self.assertEqual(_normalize_placement_status('Eligible'), 'Placement ready')

    def test_sql_hold_maps_to_can_improve(self):
        self.assertEqual(_normalize_placement_status('Hold'), 'Can Improve')

    def test_sql_not_eligible_maps_to_not_placement_ready(self):
        self.assertEqual(_normalize_placement_status('Not Eligible'), 'Not Placement ready')

    def test_ui_labels_pass_through(self):
        self.assertEqual(_normalize_placement_status('Placement ready'), 'Placement ready')

    def test_empty_returns_unknown(self):
        self.assertEqual(_normalize_placement_status(None), 'Unknown')
