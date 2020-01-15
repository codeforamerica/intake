import random
import logging
from unittest.mock import patch
from django.urls import reverse
from formation import fields
from markupsafe import escape
from intake.tests.views.test_applicant_form_view_base \
    import ApplicantFormViewBaseTestCase
from intake.views.county_application_view import WARNING_FLASH_MESSAGE
from intake.tests import mock, factories
from intake.models import County
from project.tests.assertions import assertInLogsCount


class TestCountyApplicationNoWarningsView(ApplicantFormViewBaseTestCase):
    view_name = 'intake-confirm'

    def test_get_with_no_applicant(self):
        self.set_form_session_data(
            counties=['contracosta'], create_applicant=False)
        response = self.client.get(reverse(self.view_name))
        self.assertRedirects(response, reverse('intake-apply'))

    def test_redirects_if_no_counties_in_session(self):
        self.set_form_session_data(counties=[])
        response = self.client.get(reverse(self.view_name))
        self.assertRedirects(response, reverse('intake-apply'))

    def test_can_get_form_for_counties(self):
        self.set_form_session_data(counties=['alameda', 'contracosta'])
        response = self.client.get(reverse(self.view_name))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Apply to Clear My Record',
                      response.content.decode('utf-8'))
        self.assertNotContains(response, "This field is required.")
        self.assertNotContains(response, "warninglist")
        form = response.context_data['form']
        self.assertFalse(form.is_bound())
        for key in form.get_field_keys():
            self.assertContains(response, key)

    def test_can_get_form_filled_with_existing_data(self):
        self.set_form_session_data(
            counties=['alameda', 'contracosta'],
            first_name='Seven', middle_name='of', last_name='Nine')
        response = self.client.get(reverse(self.view_name))
        self.assertEqual(response.status_code, 200)
        form = response.context_data['form']
        self.assertTrue(form.is_bound())
        self.assertContains(response, 'Seven')
        self.assertContains(response, 'Nine')

    def test_validation_warnings(self):
        self.set_form_session_data(counties=['sanfrancisco'])
        response = self.client.fill_form(
            reverse(self.view_name),
            **mock.fake.sf_pubdef_answers(ssn=''))
        self.assertRedirects(response, reverse('intake-review'))

    def test_invalid_post_shows_errors(self):
        self.set_form_session_data(counties=['sanfrancisco'])
        response = self.client.fill_form(
            reverse(self.view_name),
            **mock.fake.sf_pubdef_answers(first_name=''))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, escape(fields.FirstName.is_required_error_message))

    def test_bad_contact_data_shows_expected_errors(self):
        self.be_anonymous()
        answers = mock.fake.contra_costa_county_form_answers()
        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=['contracosta'])

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

    def test_shows_counties_where_applying(self):
        self.set_form_session_data(counties=['sanfrancisco'])
        response = self.client.get(reverse(self.view_name))
        self.assertContains(
            response, "You are applying for help in San Francisco.")

    def test_can_go_back_and_reset_counties(self):
        self.be_anonymous()
        county_slugs = list(
            County.objects.get_county_choices_query().values_list(
                'slug', flat=True))
        first_choices = random.sample(county_slugs, 2)
        second_choices = [random.choice(county_slugs)]
        self.client.fill_form(
            reverse('intake-apply'), counties=first_choices, follow=True)
        county_setting = self.client.session['form_in_progress']['counties']
        self.assertEqual(county_setting, first_choices)
        self.client.fill_form(
            reverse('intake-apply'), counties=second_choices, follow=True)
        county_setting = self.client.session['form_in_progress']['counties']
        self.assertEqual(county_setting, second_choices)

    def test_logs_page_complete_event(self):
        self.set_form_session_data(counties=['contracosta'])
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.client.fill_form(
                reverse(self.view_name),
                **mock.fake.cc_pubdef_answers())
        assertInLogsCount(
            logs, {
                'event_name=application_page_complete': 1,
                'event_name=application_started': 0,
                'event_name=application_submitted': 0,
                'event_name=application_errors': 0,
            })

    def test_logs_validation_errors_event(self):
        self.set_form_session_data(counties=['sanfrancisco'])
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.client.fill_form(
                reverse(self.view_name),
                **mock.fake.sf_pubdef_answers(first_name=''))
        assertInLogsCount(
            logs, {
                'event_name=application_page_complete': 0,
                'event_name=application_started': 0,
                'event_name=application_submitted': 0,
                'event_name=application_errors': 1,
            })

    def test_saves_form_data_to_session(self):
        self.set_form_session_data(counties=['contracosta'])
        self.client.fill_form(
            reverse(self.view_name),
            **mock.fake.cc_pubdef_answers(first_name="Marzipan"))
        form_data = self.get_form_session_data()
        self.assertEqual(form_data.get('first_name'), ["Marzipan"])


class TestCountyApplicationView(TestCountyApplicationNoWarningsView):
    view_name = 'intake-county_application'

    @patch(
        'intake.services.submissions.send_confirmation_notifications')
    def test_validation_warnings(self, send_confirmation):
        applicant = factories.ApplicantFactory.create()
        self.set_form_session_data(
            counties=['sanfrancisco'], applicant_id=applicant.id)
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            response = self.client.fill_form(
                reverse(self.view_name),
                **mock.fake.sf_pubdef_answers(ssn=''))
        self.assertRedirects(
            response, reverse('intake-confirm'), fetch_redirect_response=False)
        response = self.client.get(response.url)
        self.assertContains(response, escape(WARNING_FLASH_MESSAGE))
        self.assertContains(
            response,
            escape(
                fields.SocialSecurityNumberField.is_recommended_error_message))
        send_confirmation.assert_not_called()
        assertInLogsCount(
            logs, {
                'event_name=application_page_complete': 1,
                'event_name=application_started': 0,
                'event_name=application_submitted': 0,
                'event_name=application_errors': 0,
            })


class TestCountyApplicationReviewView(ApplicantFormViewBaseTestCase):
    view_name = 'intake-review'

    def test_get_with_no_applicant(self):
        self.set_form_session_data(
            counties=['contracosta'], create_applicant=False)
        response = self.client.get(reverse(self.view_name))
        self.assertRedirects(response, reverse('intake-apply'))

    def test_redirects_if_no_counties_in_session(self):
        self.set_form_session_data(counties=[])
        response = self.client.get(reverse(self.view_name))
        self.assertRedirects(response, reverse('intake-apply'))

    def test_redirects_if_form_session_data_missing(self):
        self.set_form_session_data(
            counties=['contracosta'])
        with self.assertLogs(
                'project.services.logging_service', logging.ERROR) as logs:
            response = self.client.get(reverse(self.view_name))
        self.assertEqual(1, len(logs.output))
        self.assertIn('application_error', logs.output[0])
        self.assertRedirects(response, reverse('intake-county_application'))

    def test_invalid_post_doesnt_show_error_message(self):
        self.set_form_session_data(
            counties=['contracosta'],
            **mock.fake.cc_pubdef_answers()
        )
        response = self.client.fill_form(
            reverse(self.view_name),
            submit_action='gobbledygook')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response, escape(
                fields.ApplicationReviewActions.is_required_error_message))

    def test_needs_letter_post_redirects_to_write_letter_page(self):
        self.set_form_session_data(
            counties=['alameda'],
            **mock.fake.a_pubdef_answers())
        response = self.client.fill_form(
            reverse(self.view_name),
            submit_action='approve_application')
        self.assertRedirects(response, reverse('intake-write_letter'))

    def test_successful_post_redirects_to_thanks_page(self):
        self.set_form_session_data(
            counties=['contracosta'],
            **mock.fake.cc_pubdef_answers())
        response = self.client.fill_form(
            reverse(self.view_name),
            submit_action='approve_application')
        self.assertRedirects(response, reverse('intake-thanks'))

    def test_needs_rap_sheet_redirects_to_rap_sheet_page(self):
        self.set_form_session_data(
            counties=['alameda'],
            **mock.fake.ebclc_answers())
        response = self.client.fill_form(
            reverse(self.view_name),
            submit_action='approve_application')
        self.assertRedirects(response, reverse('intake-rap_sheet'))

    def test_shows_counties_where_applying(self):
        self.set_form_session_data(
            counties=['sanfrancisco'],
            **mock.fake.sf_pubdef_answers())
        response = self.client.get(reverse(self.view_name))
        self.assertContains(
            response, "You are applying for help in San Francisco.")

    def test_logs_page_complete_event(self):
        self.set_form_session_data(
            counties=['contracosta'],
            **mock.fake.cc_pubdef_answers())
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.client.fill_form(
                reverse(self.view_name),
                submit_action='approve_application')
        assertInLogsCount(
            logs, {
                'event_name=application_page_complete': 1,
                'event_name=application_started': 0,
                'event_name=application_submitted': 1,
                'event_name=application_errors': 0,
            })

    def test_logs_validation_errors_event(self):
        self.set_form_session_data(
            counties=['contracosta'],
            **mock.fake.cc_pubdef_answers())
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.client.fill_form(
                reverse(self.view_name),
                submit_action='gobbledygook')
        assertInLogsCount(
            logs, {
                'event_name=application_page_complete': 0,
                'event_name=application_started': 0,
                'event_name=application_submitted': 0,
                'event_name=application_errors': 1,
            })
