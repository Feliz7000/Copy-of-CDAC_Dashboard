from django.test import SimpleTestCase
from django.urls import resolve, reverse


class UserUrlTests(SimpleTestCase):
    def test_user_bulk_upload_url_resolves(self):
        match = resolve('/api/users/bulk/users_upload/')
        self.assertEqual(match.url_name, 'user-bulk-users-upload')

    def test_token_obtain_pair_url(self):
        self.assertEqual(reverse('token_obtain_pair'), '/api/token/')
