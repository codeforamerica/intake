from datetime import datetime, timezone
from unittest.mock import Mock
from django.test import TestCase
from intake import models, groups
from user_accounts.models import Organization
from user_accounts.tests.factories import profile_for_org_and_group_names
from project.fixtures_index import ESSENTIAL_DATA_FIXTURES


class TestApplicationNote(TestCase):

    fixtures = ESSENTIAL_DATA_FIXTURES

    def test___str___with_no_user_first_name(self):
        # datetime.now(timezone.utc)
        mock_user = Mock(
            first_name='',
            username='test@codeforamerica.org')
        mock_note = Mock(
            user=mock_user,
            created=datetime(
                year=1920, month=8, day=26, hour=16, tzinfo=timezone.utc),
            body='The 19th Amendment was signed')
        result = models.ApplicationNote.__str__(self=mock_note)
        self.assertEqual(
            result,
            str('Aug 26, 8:00 AM The 19th Amendment was signed '
                '-test@codeforamerica.org'))

    def test_custom_view_permission_works_as_expected(self):
        org = Organization.objects.get(slug='cfa')
        profile = profile_for_org_and_group_names(
            org, group_names=[
                groups.FOLLOWUP_STAFF, groups.APPLICATION_REVIEWERS],
            is_staff=True)
        # this does not work with 'view_application_note', which fails to add
        # to the group
        self.assertTrue(profile.user.has_perm('intake.add_applicationnote'))
