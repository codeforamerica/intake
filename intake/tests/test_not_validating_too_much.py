from unittest.mock import patch
from django.urls import reverse
from django.test import TestCase
from django.conf import settings
from user_accounts.models import Organization
from intake.tests.factories import FormSubmissionWithOrgsFactory, make_apps_for
from user_accounts.tests.factories import app_reviewer


class TestDontValidateTooMuch(TestCase):
    fixtures = ['counties', 'organizations']

    @patch('formation.base.BindParseValidate.validate')
    def test_factory_doesnt_initiate_validation(self, validate):
        cfa = Organization.objects.get(slug='cfa')
        sub = FormSubmissionWithOrgsFactory(organizations=[cfa])
        validate.assert_not_called()

    @patch('formation.base.BindParseValidate.validate')
    def test_application_detail_doesnt_initiate_validation(self, validate):
        profile = app_reviewer('cc_pubdef')
        app = make_apps_for('cc_pubdef', count=1)[0]
        self.client.login(
            username=profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        self.client.get(reverse(
            'intake-app_detail', kwargs=dict(
                submission_id=app.form_submission_id)))
        validate.assert_not_called()
