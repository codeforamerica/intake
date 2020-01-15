import logging
from unittest.mock import patch, Mock
from django.urls import reverse
from project.fixtures_index import ESSENTIAL_DATA_FIXTURES
from user_accounts.tests.base_testcases import AuthIntegrationTestCase
from intake.views.applicant_form_view_base import ApplicantFormViewBase
from intake import models
from user_accounts.models import Organization
from intake.tests.mock import fake
from intake.tests import factories
from project.tests.assertions import assertInLogsCount


class ApplicantFormViewBaseTestCase(AuthIntegrationTestCase):
    fixtures = ESSENTIAL_DATA_FIXTURES

    def setUp(self):
        super().setUp()
        self.send_confirmations_patcher = patch(
            'intake.services.submissions.send_confirmation_notifications')
        self.send_confirmations = self.send_confirmations_patcher.start()

    def tearDown(self):
        self.send_confirmations_patcher.stop()
        super().tearDown()

    def set_form_session_data(self, create_applicant=True, **data):
        applicant = data.pop('applicant', None)
        if create_applicant and not applicant:
            applicant = factories.ApplicantFactory.create()
        if applicant:
            self.set_session(applicant_id=applicant.id)
        self.set_querydictifiable_session(**{
            ApplicantFormViewBase.session_key: data})

    def get_form_session_data(self):
        return self.client.session.get(ApplicantFormViewBase.session_key)


class TestApplicantFormViewBase(ApplicantFormViewBaseTestCase):

    def test_doesnt_redirect_if_has_counties_in_session(self):
        mock_view_instance = Mock(
            session_data={'counties': ['alameda', 'contracosta']})
        response = ApplicantFormViewBase.check_for_session_based_redirects(
            mock_view_instance)
        self.assertEqual(response, None)

    @patch('intake.models.County.get_receiving_agency')
    def test_get_receiving_organizations_if_no_attribute(self, get_agency):
        counties = models.County.objects.all()[:2]
        orgs = [
            Organization.objects.filter(county_id=county.id).first()
            for county in counties]
        get_agency.side_effect = orgs
        mock_view_instance = Mock(
            receiving_organizations=None, counties=counties)
        results = ApplicantFormViewBase.get_receiving_organizations(
            mock_view_instance, Mock())
        self.assertEqual(get_agency.call_count, 2)
        self.assertListEqual(orgs, results)
        self.assertListEqual(
            orgs, mock_view_instance.receiving_organizations)

    @patch('intake.models.County.get_receiving_agency')
    def test_get_receiving_organizations_if_exists(self, get_agency):
        counties = models.County.objects.all()[:2]
        orgs = [
            Organization.objects.filter(county_id=county.id).first()
            for county in counties]
        get_agency.side_effect = orgs
        mock_view_instance = Mock(
            receiving_organizations=orgs, counties=counties)
        results = ApplicantFormViewBase.get_receiving_organizations(
            mock_view_instance, Mock())
        self.assertEqual(get_agency.call_count, 0)
        self.assertListEqual(orgs, results)
        self.assertListEqual(
            orgs, mock_view_instance.receiving_organizations)

    @patch('intake.services.messages_service.flash_success')
    @patch('intake.services.submissions.send_to_newapps_bundle_if_needed')
    @patch('intake.services.submissions.create_submission')
    def test_finalize_application_actions(
            self, create_sub, send_to_newapps, flash_success):
        self.set_form_session_data(counties=['contracosta'])
        answers = fake.contra_costa_county_form_answers()
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.client.fill_form(
                reverse('intake-county_application'), **answers)
            self.client.fill_form(
                reverse('intake-review'),
                submit_action='approve_application')
        self.assertEqual(create_sub.call_count, 1)
        self.assertEqual(send_to_newapps.call_count, 1)
        self.assertEqual(self.send_confirmations.call_count, 1)
        self.assertEqual(flash_success.call_count, 1)
        assertInLogsCount(
            logs, {
                'event_name=application_submitted': 1,
                'event_name=application_page_complete': 2,
                'event_name=application_started': 0,
                'event_name=application_errors': 0,
            })
