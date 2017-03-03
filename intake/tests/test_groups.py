from intake.tests.base_testcases import IntakeDataTestCase
from django.contrib.auth.models import Group
from intake import groups


class TestGroups(IntakeDataTestCase):

    fixtures = [
        'counties', 'organizations', 'mock_profiles'
    ]

    def test_followup_staff_group(self):
        user = self.be_cfa_user()
        group = Group.objects.get(name=groups.FOLLOWUP_STAFF)
        self.assertIn(group, user.groups.all())

    def test_application_reviewers_group(self):
        user = self.be_cfa_user()
        group = Group.objects.get(name=groups.APPLICATION_REVIEWERS)
        self.assertIn(group, user.groups.all())
