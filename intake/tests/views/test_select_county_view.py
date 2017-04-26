from unittest.mock import patch
from django.core.urlresolvers import reverse
from markupsafe import escape
from intake.views.applicant_form_view_base import ApplicantFormViewBase
from django.http.request import QueryDict
from intake import utils, models, constants
from formation import fields
from intake.tests.views.test_applicant_form_view_base \
    import ApplicantFormViewBaseTestCase
from intake.tests import factories


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

    def test_anonymous_user_can_access_county_view(self):
        self.be_anonymous()
        county_view = self.client.get(
            reverse('intake-apply'))
        for slug, description in constants.COUNTY_CHOICES:
            self.assertContains(county_view, slug)
            self.assertContains(county_view, escape(description))

        applicant_id = self.client.session.get('applicant_id')
        self.assertIsNone(applicant_id)

    def test_anonymous_user_can_submit_county_selection(self):
        self.be_anonymous()
        response = self.client.fill_form(
            reverse('intake-apply'),
            counties=['contracosta'],
            confirm_county_selection='yes',
            headers={'HTTP_USER_AGENT': 'tester'})
        self.assertRedirects(response, reverse('intake-county_application'))
        applicant_id = self.client.session.get('applicant_id')
        self.assertTrue(applicant_id)
        applicant = models.Applicant.objects.get(id=applicant_id)
        self.assertTrue(applicant)
        self.assertTrue(applicant.visitor_id)
        visitor = models.Visitor.objects.get(id=applicant.visitor_id)
        self.assertTrue(visitor)
        events = list(applicant.events.order_by('time'))
        self.assertEqual(len(events), 2)
        event = events[0]
        self.assertEqual(event.name,
                         models.ApplicationEvent.APPLICATION_STARTED)
        self.assertIn('user_agent', event.data)
        self.assertEqual(event.data['user_agent'], 'tester')
        self.assertIn('referrer', event.data)
        self.assertEqual(event.data['counties'], ['contracosta'])

    def test_creates_applicant(self):
        response = self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'],
            confirm_county_selection='yes')
        self.assertTrue(response.wsgi_request.applicant.id)

    def test_create_applicant_with_existing_visitor_and_applicant(self):
        existing_applicant = factories.ApplicantFactory()
        self.set_session(visitor_id=existing_applicant.visitor.id)
        response = self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'],
            confirm_county_selection='yes')
        self.assertEqual(
            response.wsgi_request.applicant, existing_applicant)
