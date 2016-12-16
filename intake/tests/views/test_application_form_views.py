from django.test import TestCase, override_settings
import logging
import random
from user_accounts.tests.test_auth_integration import AuthIntegrationTestCase
from intake.tests.base_testcases import IntakeDataTestCase

from unittest.mock import patch, Mock
from intake.tests import mock
from intake import models, constants
from django.core.urlresolvers import reverse
from django.utils import html as html_utils
from formation import forms
from intake.views import session_view_base


class TestSelectCountyView(AuthIntegrationTestCase):

    def test_anonymous_user_can_access_county_view(self):
        self.be_anonymous()
        county_view = self.client.get(
            reverse('intake-apply'))
        for slug, description in constants.COUNTY_CHOICES:
            self.assertContains(county_view, slug)
            self.assertContains(county_view, html_utils.escape(description))

        applicant_id = self.client.session.get('applicant_id')
        self.assertIsNone(applicant_id)

    def test_anonymous_user_can_submit_county_selection(self):
        self.be_anonymous()
        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=['contracosta'],
            headers={'HTTP_USER_AGENT': 'tester'})
        self.assertRedirects(result, reverse('intake-county_application'))
        applicant_id = self.client.session.get('applicant_id')
        self.assertTrue(applicant_id)
        applicant = models.Applicant.objects.get(id=applicant_id)
        self.assertTrue(applicant)
        self.assertTrue(applicant.visitor_id)
        visitor = models.Visitor.objects.get(id=applicant.visitor_id)
        self.assertTrue(visitor)
        events = list(applicant.events.all())
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.name,
                         models.ApplicationEvent.APPLICATION_STARTED)
        self.assertIn('ip', event.data)
        self.assertIn('user_agent', event.data)
        self.assertEqual(event.data['user_agent'], 'tester')
        self.assertIn('referrer', event.data)
        self.assertEqual(event.data['counties'], ['contracosta'])

    def test_anonymous_user_cannot_submit_empty_county_selection(self):
        self.be_anonymous()
        result = self.client.fill_form(
            reverse('intake-apply'))
        self.assertEqual(result.status_code, 200)
        form = result.context_data['form']
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)


class TestMultiCountyApplication(AuthIntegrationTestCase):

    fixtures = ['counties', 'organizations']

    @patch(
        'intake.services.submissions.send_confirmation_notifications')
    @patch(
        'intake.views.session_view_base.notifications'
        '.slack_new_submission.send')
    def test_sf_application_redirects_if_missing_recommended_fields(
            self, slack, send_confirmation):
        self.be_anonymous()
        applicant = models.Applicant()
        applicant.save()
        sanfrancisco = constants.Counties.SAN_FRANCISCO
        answers = mock.fake.sf_county_form_answers()
        answers['ssn'] = ''
        self.set_session(
            form_in_progress=dict(counties=[sanfrancisco]),
            applicant_id=applicant.id
            )
        response = self.client.fill_form(
            reverse('intake-county_application'),
            follow=True,
            **answers
            )
        self.assertEqual(
            response.wsgi_request.path, reverse('intake-confirm'))
        form = response.context_data['form']
        self.assertTrue(form.warnings)
        self.assertFalse(form.errors)
        self.assertIn('ssn', form.warnings)
        slack.assert_not_called()
        send_confirmation.assert_not_called()
        submitted_event_count = applicant.events.filter(
            name=models.ApplicationEvent.APPLICATION_SUBMITTED).count()
        self.assertEqual(0, submitted_event_count)

    @patch(
        'intake.services.submissions.send_confirmation_notifications')
    @patch(
        'intake.views.session_view_base.notifications'
        '.slack_new_submission.send')
    def test_can_apply_to_contra_costa_alone(self, slack, send_confirmation):
        self.be_anonymous()
        contracosta = constants.Counties.CONTRA_COSTA
        cc_pubdef = constants.Organizations.COCO_PUBDEF
        answers = mock.fake.contra_costa_county_form_answers()

        county_fields = forms.ContraCostaFormSpec.fields
        other_county_fields = \
            forms.SanFranciscoCountyFormSpec.fields \
            | forms.OtherCountyFormSpec.fields
        county_specific_fields = county_fields - other_county_fields
        county_specific_field_names = [
            Field.context_key for Field in county_specific_fields]
        other_county_fields = other_county_fields - county_fields
        other_county_field_names = [
            Field.context_key for Field in other_county_fields]

        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=[contracosta])
        self.assertRedirects(result, reverse('intake-county_application'))
        result = self.client.get(reverse('intake-county_application'))

        for field_name in county_specific_field_names:
            self.assertContains(result, field_name)

        for field_name in other_county_field_names:
            self.assertNotContains(result, field_name)

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)
        self.assertRedirects(result, reverse('intake-thanks'))
        applicant_id = self.client.session.get('applicant_id')
        self.assertTrue(applicant_id)
        applicant = models.Applicant.objects.get(id=applicant_id)

        submissions = list(applicant.form_submissions.all())
        self.assertEqual(1, len(submissions))
        submission = submissions[0]

        county_slugs = [county.slug for county in submission.get_counties()]
        self.assertListEqual(county_slugs, [contracosta])
        org_slugs = [org.slug for org in submission.organizations.all()]
        self.assertListEqual(org_slugs, [cc_pubdef])

        submitted_event_count = applicant.events.filter(
            name=models.ApplicationEvent.APPLICATION_SUBMITTED).count()

        self.assertEqual(1, submitted_event_count)

    @patch(
        'intake.services.submissions.send_confirmation_notifications')
    @patch(
        'intake.views.session_view_base.notifications'
        '.slack_new_submission.send')
    def test_contra_costa_errors_properly(self, slack, send_confirmation):
        self.be_anonymous()
        contracosta = constants.Counties.CONTRA_COSTA
        answers = mock.fake.contra_costa_county_form_answers()
        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=[contracosta])
        required_fields = forms.ContraCostaFormSpec.required_fields

        # check that leaving out any required field returns an error on that
        # field
        for required_field in required_fields:
            if hasattr(required_field, 'subfields'):
                continue
            field_key = required_field.context_key
            bad_data = answers.copy()
            bad_data[field_key] = ''
            result = self.client.fill_form(
                reverse('intake-county_application'),
                **bad_data)
            self.assertContains(
                result, required_field.is_required_error_message)

        # check for the preferred contact methods validator
        bad_data = answers.copy()
        bad_data['contact_preferences'] = ['prefers_email', 'prefers_sms']
        bad_data['email'] = ''
        bad_data['phone_number'] = ''
        result = self.client.fill_form(
            reverse('intake-county_application'),
            **bad_data)
        self.assertTrue(result.context_data['form'].email.errors)
        self.assertTrue(result.context_data['form'].phone_number.errors)

        event = models.ApplicationEvent.objects.filter(
            applicant_id=self.client.session['applicant_id'],
            name=models.ApplicationEvent.APPLICATION_ERRORS).first()

        self.assertDictEqual(
            result.context_data['form'].get_serialized_errors(),
            event.data['errors'])

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)
        self.assertRedirects(result, reverse('intake-thanks'))
        self.assertTrue(slack.called)
        self.assertTrue(send_confirmation.called)

    @patch(
        'intake.services.submissions.send_confirmation_notifications')
    @patch(
        'intake.views.session_view_base.notifications'
        '.slack_new_submission.send')
    def test_alameda_pubdef_application_redirects_to_declaration_letter(
            self, slack, send_confirmation):

        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        answers = mock.fake.alameda_pubdef_answers()
        result = self.client.fill_form(
            reverse('intake-apply'), counties=[alameda])
        self.assertRedirects(result, reverse('intake-county_application'))
        result = self.client.get(reverse('intake-county_application'))

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)

        self.assertRedirects(result, reverse("intake-write_letter"))
        slack.assert_not_called()
        send_confirmation.assert_not_called()

    @patch(
        'intake.services.submissions.send_confirmation_notifications')
    @patch(
        'intake.views.session_view_base.notifications.slack_new_submission'
        '.send')
    def test_invalid_alameda_application_returns_same_page_with_error(
            self, slack, send_confirmation):
        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        answers = mock.fake.alameda_pubdef_answers()
        answers['monthly_income'] = ""
        result = self.client.fill_form(
            reverse('intake-apply'), counties=[alameda])
        self.assertRedirects(result, reverse('intake-county_application'))
        result = self.client.get(reverse('intake-county_application'))

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.wsgi_request.path,
                         reverse('intake-county_application'))
        self.assertTrue(result.context_data['form'].errors)
        slack.assert_not_called()
        send_confirmation.assert_not_called()

        event = models.ApplicationEvent.objects.filter(
            applicant_id=self.client.session['applicant_id'],
            name=models.ApplicationEvent.APPLICATION_ERRORS).first()

        self.assertDictEqual(
            result.context_data['form'].get_serialized_errors(),
            event.data['errors'])

    @patch(
        'intake.services.submissions.send_confirmation_notifications')
    @patch(
        'intake.views.session_view_base.notifications'
        '.slack_new_submission.send')
    def test_valid_ebclc_application_returns_rap_sheet_page(
            self, slack, send_confirmation):
        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        answers = mock.fake.ebclc_answers()
        result = self.client.fill_form(
            reverse('intake-apply'), counties=[alameda])
        self.assertRedirects(result, reverse('intake-county_application'))
        result = self.client.get(reverse('intake-county_application'))

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)
        self.assertRedirects(
            result, reverse("intake-rap_sheet"))
        self.assertTrue(slack.called)
        self.assertTrue(send_confirmation.called)

    @patch(
        'intake.services.submissions.send_confirmation_notifications')
    @patch(
        'intake.views.session_view_base.notifications'
        '.slack_new_submission.send')
    def test_invalid_ebclc_application_returns_same_page_with_error(
            self, slack, send_confirmation):
        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        answers = mock.fake.ebclc_answers()
        answers['monthly_income'] = ""
        result = self.client.fill_form(
            reverse('intake-apply'), counties=[alameda])
        self.assertRedirects(result, reverse('intake-county_application'))
        result = self.client.get(reverse('intake-county_application'))

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.wsgi_request.path,
                         reverse('intake-county_application'))
        self.assertTrue(result.context_data['form'].errors)
        slack.assert_not_called()
        send_confirmation.assert_not_called()

        event = models.ApplicationEvent.objects.filter(
            applicant_id=self.client.session['applicant_id'],
            name=models.ApplicationEvent.APPLICATION_ERRORS).first()

        self.assertDictEqual(
            result.context_data['form'].get_serialized_errors(),
            event.data['errors'])

    def test_can_go_back_and_reset_counties(self):
        self.be_anonymous()
        county_slugs = [slug for slug, text in constants.COUNTY_CHOICES]
        first_choices = random.sample(county_slugs, 2)
        second_choices = [random.choice(county_slugs)]
        self.client.fill_form(
            reverse('intake-apply'),
            counties=first_choices,
            follow=True)
        county_setting = self.client.session['form_in_progress']['counties']
        self.assertEqual(county_setting, first_choices)

        self.client.fill_form(
            reverse('intake-apply'),
            counties=second_choices,
            follow=True)
        county_setting = self.client.session['form_in_progress']['counties']
        self.assertEqual(county_setting, second_choices)

    @patch('intake.notifications.slack_simple.send')
    def test_no_counties_found_error_sends_slack_and_redirects(self, slack):
        self.be_anonymous()
        response = self.client.get(reverse('intake-county_application'))
        self.assertRedirects(
            response, reverse('intake-home'), fetch_redirect_response=False)
        self.assertTrue(slack.called)
        response = self.client.get(response.url)
        expected_flash_message = html_utils.conditional_escape(
            session_view_base.GENERIC_USER_ERROR_MESSAGE)
        self.assertContains(response, expected_flash_message)


class TestDeclarationLetterView(AuthIntegrationTestCase):

    fixtures = ['counties', 'organizations', 'mock_profiles']

    @patch(
        'intake.services.submissions.send_confirmation_notifications')
    @patch(
        'intake.views.session_view_base.notifications'
        '.slack_new_submission.send')
    def test_expected_success(self, slack, send_confirmation):
        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        self.client.fill_form(
            reverse('intake-apply'), counties=[alameda], follow=True)
        answers = mock.fake.alameda_pubdef_answers(first_name="RandomName")
        self.client.fill_form(
            reverse('intake-county_application'), follow=True, **answers)

        declaration_answers = mock.fake.declaration_letter_answers()
        result = self.client.fill_form(
            reverse('intake-write_letter'), **declaration_answers)

        self.assertRedirects(result, reverse('intake-review_letter'))

        form_data = self.client.session.get('form_in_progress')
        for key, value in declaration_answers.items():
            self.assertIn(key, form_data)
            session_value = form_data[key]
            self.assertEqual(session_value, value)

        slack.assert_not_called()
        send_confirmation.assert_not_called()

    @patch(
        'intake.services.submissions.send_confirmation_notifications')
    @patch(
        'intake.views.session_view_base.notifications'
        '.slack_new_submission.send')
    def test_invalid_letter_returns_same_page(self, slack, send_confirmation):
        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        self.client.fill_form(
            reverse('intake-apply'), counties=[alameda], follow=True)
        answers = mock.fake.alameda_pubdef_answers(first_name="RandomName")
        self.client.fill_form(
            reverse('intake-county_application'), follow=True, **answers)

        slack.assert_not_called()
        send_confirmation.assert_not_called()

        declaration_answers = mock.fake.declaration_letter_answers(
            declaration_letter_why="")

        result = self.client.fill_form(
            reverse('intake-write_letter'), **declaration_answers)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.wsgi_request.path,
                         reverse('intake-write_letter'))

        self.assertTrue(result.context_data['form'].errors)

        event = models.ApplicationEvent.objects.filter(
            applicant_id=self.client.session['applicant_id'],
            name=models.ApplicationEvent.APPLICATION_ERRORS).first()

        self.assertDictEqual(
            result.context_data['form'].get_serialized_errors(),
            event.data['errors'])

    def test_no_existing_data(self):
        self.be_anonymous()
        with self.assertLogs(
                'intake.views.application_form_views', level=logging.WARN):
            result = self.client.get(reverse('intake-write_letter'))
            self.assertRedirects(result, reverse('intake-apply'))


class TestDeclarationLetterReviewPage(AuthIntegrationTestCase):

    fixtures = ['counties', 'organizations', 'mock_profiles']

    def test_get_with_expected_data(self):
        self.be_anonymous()
        mock_letter = mock.fake.declaration_letter_answers()
        mock_answers = mock.fake.alameda_pubdef_answers(
            first_name="foo", last_name="bar")
        counties = {'counties': constants.Counties.ALAMEDA}
        session_data = {}
        for other_data in [counties, mock_answers, mock_letter]:
            session_data.update(other_data)
        self.set_session(
            form_in_progress=session_data)
        response = self.client.get(reverse('intake-review_letter'))
        self.assertContains(response, 'To Whom It May Concern')
        for portion in mock_letter.values():
            self.assertContains(response, html_utils.escape(portion))
        self.assertContains(response, 'Sincerely,')
        self.assertContains(response, 'Foo')
        self.assertContains(response, 'Bar')
        self.assertContains(
            response, 'name="submit_action" value="approve_letter"')
        self.assertContains(
            response, 'name="submit_action" value="edit_letter"')

    def test_get_with_no_existing_data(self):
        self.be_anonymous()
        with self.assertLogs(
                'intake.views.application_form_views', level=logging.WARN):
            result = self.client.get(reverse('intake-review_letter'))
            self.assertRedirects(result, reverse('intake-apply'))

    def test_post_edit_letter(self):
        self.be_anonymous()
        mock_letter = mock.fake.declaration_letter_answers()
        mock_answers = mock.fake.alameda_pubdef_answers()
        counties = {'counties': constants.Counties.ALAMEDA}
        session_data = {}
        for other_data in [counties, mock_answers, mock_letter]:
            session_data.update(other_data)
        self.set_session(
            form_in_progress=session_data,
            applicant_id=2)
        response = self.client.fill_form(
            reverse('intake-review_letter'),
            submit_action="edit_letter")
        self.assertRedirects(response, reverse('intake-write_letter'))
        applicant_id = self.client.session.get('applicant_id')
        self.assertTrue(applicant_id)
        self.assertEqual(models.FormSubmission.objects.filter(
            applicant_id=applicant_id).count(), 0)

    @patch(
        'intake.services.submissions.send_confirmation_notifications')
    @patch(
        'intake.views.session_view_base.notifications'
        '.slack_new_submission.send')
    def test_post_approve_letter(self, slack, send_confirmation):
        self.be_anonymous()
        applicant = models.Applicant()
        applicant.save()
        alameda = constants.Counties.ALAMEDA
        mock_letter = mock.fake.declaration_letter_answers()
        mock_answers = mock.fake.alameda_pubdef_answers()
        counties = {'counties': [alameda]}
        session_data = {}
        for other_data in [counties, mock_answers, mock_letter]:
            session_data.update(other_data)
        self.set_session(
            form_in_progress=session_data,
            applicant_id=applicant.id)
        response = self.client.fill_form(
            reverse('intake-review_letter'),
            submit_action="approve_letter")
        self.assertRedirects(response, reverse('intake-thanks'))

        applicant_id = self.client.session.get('applicant_id')
        self.assertTrue(applicant_id)

        submissions = list(models.FormSubmission.objects.filter(
            applicant_id=applicant_id))
        self.assertEqual(len(submissions), 1)
        submission = submissions[0]
        county_slugs = [county.slug for county in submission.get_counties()]
        self.assertListEqual(county_slugs, [alameda])
        self.assertIn(self.a_pubdef, submission.organizations.all())
        self.assertEqual(submission.organizations.count(), 1)
        self.assertEqual(submission.organizations.first().county.slug, alameda)
        filled_pdf_count = models.FilledPDF.objects.count()
        self.assertEqual(filled_pdf_count, 0)
        self.be_apubdef_user()
        resp = self.client.get(reverse("intake-app_index"))
        url = reverse(
            "intake-app_detail",
            kwargs={'submission_id': submission.id})
        self.assertContains(resp, url)
        self.assertTrue(slack.called)
        self.assertTrue(send_confirmation.called)


class TestThanks(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations',
        'mock_profiles',
        'mock_2_submissions_to_cc_pubdef']

    def test_anonymous_with_no_application_redirected_to_home(self):
        self.be_anonymous()
        response = self.client.get(reverse('intake-thanks'))
        self.assertRedirects(
            response, reverse('intake-home'), fetch_redirect_response=False)

    def test_existing_application_has_org_data(self):
        self.be_anonymous()
        app = models.Applicant()
        app.save()
        sub = models.FormSubmission.objects.all().first()
        sub.applicant_id = app.id
        sub.save()
        self.set_session(applicant_id=app.id)
        response = self.client.get(reverse('intake-thanks'))
        for org in sub.organizations.all():
            self.assertContains(response, html_utils.escape(org.name))


@override_settings(MIXPANEL_KEY='fake_key')
class TestRAPSheetInstructions(TestCase):

    def test_renders_with_no_session_data(self):
        response = self.client.get(reverse('intake-rap_sheet'))
        # make sure it has a link to the pdf
        self.assertNotIn('qualifies_for_fee_waiver', response.context_data)
        # make sure there aren't any unrendered variables
        self.assertNotContains(response, "{{")

    @patch(
        'intake.views.application_form_views.get_last_submission_of_applicant')
    @patch(
        'intake.views.application_form_views.RAPSheetInstructions'
        '.get_applicant_id')
    def test_pulls_relevant_info_if_session_data(self, get_app_id, get_sub):
        get_app_id.return_value = 1
        submission_mock = Mock()
        submission_mock.organizations.all.return_value = [
            'an_org', 'another_org']
        get_sub.return_value = submission_mock
        response = self.client.get(reverse('intake-rap_sheet'))
        self.assertIn('qualifies_for_fee_waiver', response.context_data)
        self.assertIn('organizations', response.context_data)
        submission_mock.qualifies_for_fee_waiver.assert_called_once_with()
