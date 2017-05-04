import random
from unittest.mock import patch
from django.core.urlresolvers import reverse
from formation import fields
from markupsafe import escape
from intake.tests.views.test_applicant_form_view_base \
    import ApplicantFormViewBaseTestCase
from intake.views.county_application_view import WARNING_FLASH_MESSAGE
from intake.tests import mock, factories
from intake import models, constants


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

    def test_needs_letter_post_redirects_to_write_letter_page(self):
        self.set_form_session_data(counties=['alameda'])
        response = self.client.fill_form(
            reverse(self.view_name),
            **mock.fake.a_pubdef_answers())
        self.assertRedirects(response, reverse('intake-write_letter'))

    def test_successful_post_redirects_to_thanks_page(self):
        self.set_form_session_data(counties=['contracosta'])
        response = self.client.fill_form(
            reverse(self.view_name),
            **mock.fake.cc_pubdef_answers())
        self.assertRedirects(response, reverse('intake-thanks'))

    def test_needs_rap_sheet_redirects_to_rap_sheet_page(self):
        self.set_form_session_data(counties=['alameda'])
        response = self.client.fill_form(
            reverse(self.view_name),
            **mock.fake.ebclc_answers())
        self.assertRedirects(response, reverse('intake-rap_sheet'))

    def test_validation_warnings(self):
        self.set_form_session_data(counties=['sanfrancisco'])
        response = self.client.fill_form(
            reverse(self.view_name),
            **mock.fake.sf_pubdef_answers(ssn=''))
        self.assertRedirects(response, reverse('intake-thanks'))

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
        contracosta = constants.Counties.CONTRA_COSTA
        answers = mock.fake.contra_costa_county_form_answers()
        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=[contracosta],
            confirm_county_selection='yes')

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
            response, "You are applying for help in San Francisco County.")

    def test_can_go_back_and_reset_counties(self):
        self.be_anonymous()
        county_slugs = [slug for slug, text in constants.COUNTY_CHOICES]
        first_choices = random.sample(county_slugs, 2)
        second_choices = [random.choice(county_slugs)]
        self.client.fill_form(
            reverse('intake-apply'),
            counties=first_choices,
            confirm_county_selection='yes',
            follow=True)
        county_setting = self.client.session['form_in_progress']['counties']
        self.assertEqual(county_setting, first_choices)

        self.client.fill_form(
            reverse('intake-apply'),
            counties=second_choices,
            confirm_county_selection='yes',
            follow=True)
        county_setting = self.client.session['form_in_progress']['counties']
        self.assertEqual(county_setting, second_choices)

    @patch('intake.services.events_service.log_form_page_complete')
    def test_logs_page_complete_event(self, event_log):
        self.set_form_session_data(counties=['contracosta'])
        self.client.fill_form(
            reverse(self.view_name),
            **mock.fake.cc_pubdef_answers())
        self.assertEqual(event_log.call_count, 1)

    @patch('intake.services.events_service.log_form_validation_errors')
    def test_logs_validation_errors_event(self, event_log):
        self.set_form_session_data(counties=['sanfrancisco'])
        self.client.fill_form(
            reverse(self.view_name),
            **mock.fake.sf_pubdef_answers(first_name=''))
        self.assertEqual(event_log.call_count, 1)

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
    @patch(
        'intake.views.applicant_form_view_base.notifications'
        '.slack_new_submission.send')
    def test_validation_warnings(self, slack, send_confirmation):
        applicant = factories.ApplicantFactory.create()
        self.set_form_session_data(
            counties=['sanfrancisco'], applicant_id=applicant.id)
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
        slack.assert_not_called()
        send_confirmation.assert_not_called()
        submitted_event_count = applicant.events.filter(
            name=models.ApplicationEvent.APPLICATION_SUBMITTED).count()
        self.assertEqual(0, submitted_event_count)
