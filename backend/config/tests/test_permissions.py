from django.test import SimpleTestCase

from config.permissions import CanManageScores, IsAdminOrHOD, IsStaffOnly


class PermissionTests(SimpleTestCase):
  def _user(self, role_name: str):
    class U:
      is_authenticated = True
      role = role_name

    return U()

  def test_staff_only_allows_faculty(self):
    perm = IsStaffOnly()
    request = type('R', (), {'user': self._user('faculty')})()
    self.assertTrue(perm.has_permission(request, None))

  def test_can_manage_scores_includes_hod(self):
    perm = CanManageScores()
    request = type('R', (), {'user': self._user('hod'), 'method': 'POST'})()
    self.assertTrue(perm.has_permission(request, None))

  def test_admin_or_hod_blocks_faculty(self):
    perm = IsAdminOrHOD()
    request = type('R', (), {'user': self._user('faculty')})()
    self.assertFalse(perm.has_permission(request, None))
