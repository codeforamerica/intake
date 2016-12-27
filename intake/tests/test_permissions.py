from intake.tests.base_testcases import IntakeDataTestCase
from intake import permissions


class TestPermissions(IntakeDataTestCase):

    fixtures = [
        'counties', 'organizations', 'mock_profiles'
        ]

    def test_can_see_followup_notes(self):
        user = self.be_cfa_user()
        self.assertTrue(
            user.has_perm(permissions.CAN_SEE_FOLLOWUP_NOTES.app_code))
