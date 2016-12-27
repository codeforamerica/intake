from datetime import datetime, timezone
from unittest.mock import Mock
from django.test import TestCase
from intake import models
from intake.tests import mock
from user_accounts.tests.mock import fake_superuser


class TestApplicationNote(TestCase):

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

    def test_deleting_submission_deletes_note(self):
        user = fake_superuser()
        submission = mock.make_submission()
        mock.make_note(user, submission.id)
        submission.delete()
        notes = models.ApplicationNote.objects.filter(user=user)
        self.assertEqual(notes.count(), 0)
