from unittest.mock import patch
from django.core.urlresolvers import reverse
from intake.views.applicant_form_view_base import ApplicantFormViewBase
from intake.tests.views.test_applicant_form_view_base \
    import ApplicantFormViewBaseTestCase
from django.http.request import QueryDict
from intake import utils
from formation import fields
from markupsafe import escape


class TestSelectCountyView(ApplicantFormViewBaseTestCase):

    def test_county_selection_saved_to_session(self):
        self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'],
            confirm_county_selection='yes')
        form_data = self.client.session.get(ApplicantFormViewBase.session_key)
        self.assertListEqual(['alameda', 'contracosta'], form_data['counties'])

    def test_county_select_persists_after_session_update(self):
        response = self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'],
            confirm_county_selection='yes')
        request = response.wsgi_request
        qdict = QueryDict('', mutable=True)
        qdict.setlist('hello', ['world'])
        utils.save_form_data_to_session(
            request, ApplicantFormViewBase.session_key, qdict)
        form_data = self.client.session.get(ApplicantFormViewBase.session_key)
        self.assertListEqual(['alameda', 'contracosta'], form_data['counties'])

    def test_select_county_redirects_to_county_application(self):
        response = self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'],
            confirm_county_selection='yes')
        self.assertRedirects(response, reverse('intake-county_application'))

    def test_no_county_confirmation_returns_and_shows_error(self):
        response = self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'])
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            escape(fields.AffirmCountySelection.is_required_error_message))

    def test_no_counties_selected_returns_error(self):
        response = self.client.fill_form(
            reverse('intake-apply'), confirm_county_selection='yes')
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, escape(fields.Counties.is_required_error_message))

    @patch('intake.services.events_service.log_form_page_complete')
    def test_logs_page_complete_event(self, event_log):
        self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'],
            confirm_county_selection='yes')
        self.assertEqual(event_log.call_count, 1)

    def test_saves_form_data_to_session(self):
        self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'],
            confirm_county_selection='yes')
        form_data = self.get_form_session_data()
        self.assertEqual(
            form_data.get('counties'), ['alameda', 'contracosta'])
        self.assertEqual(
            form_data.get('confirm_county_selection'), ['yes'])

    @patch('intake.services.events_service.log_form_validation_errors')
    def test_logs_validation_errors_event(self, event_log):
        self.client.fill_form(
            reverse('intake-apply'), confirm_county_selection='yes')
        self.assertEqual(event_log.call_count, 1)

    def test_shows_error_messages_in_flash(self):
        response = self.client.fill_form(
            reverse('intake-apply'), confirm_county_selection='yes')
        self.assertContains(
            response, escape(fields.Counties.is_required_error_message))

    def test_get_page_shows_existing_data(self):
        self.set_form_session_data(
            counties=['contracosta'])
        response = self.client.get(reverse('intake-apply'))
        checked_input = str(
            '<input type="checkbox" name="counties" value="contracosta" '
            'checked>')
        form = response.context_data['form']
        self.assertTrue(form.is_bound())
        self.assertInHTML(checked_input, response.rendered_content)
