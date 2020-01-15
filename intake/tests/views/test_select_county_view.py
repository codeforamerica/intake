import logging
from django.urls import reverse
from markupsafe import escape
from intake.views.applicant_form_view_base import ApplicantFormViewBase
from django.http.request import QueryDict
from intake import utils, models, constants
from formation import fields
from intake.tests.views.test_applicant_form_view_base \
    import ApplicantFormViewBaseTestCase
from intake.tests import factories
from intake.models import County
from project.tests.assertions import assertInLogsCount, assertInLogs


class TestSelectCountyView(ApplicantFormViewBaseTestCase):

    def test_county_selection_saved_to_session(self):
        self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'])
        form_data = self.client.session.get(ApplicantFormViewBase.session_key)
        self.assertListEqual(['alameda', 'contracosta'], form_data['counties'])

    def test_county_select_persists_after_session_update(self):
        response = self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'])
        request = response.wsgi_request
        qdict = QueryDict('', mutable=True)
        qdict.setlist('hello', ['world'])
        utils.save_form_data_to_session(
            request, ApplicantFormViewBase.session_key, qdict)
        form_data = self.client.session.get(ApplicantFormViewBase.session_key)
        self.assertListEqual(['alameda', 'contracosta'], form_data['counties'])

    def test_select_county_redirects_to_county_application(self):
        response = self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'])
        self.assertRedirects(response, reverse('intake-county_application'))

    def test_no_counties_selected_returns_error(self):
        response = self.client.fill_form(
            reverse('intake-apply'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, escape(fields.Counties.is_required_error_message))

    def test_logs_page_complete_and_application_started(self):
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.client.fill_form(
                reverse('intake-apply'), counties=['alameda', 'contracosta'])
        assertInLogsCount(
            logs, {
                'event_name=application_page_complete': 1,
                'event_name=application_started': 1,
                })
        assertInLogs(logs, 'alameda', 'contracosta')

    def test_saves_form_data_to_session(self):
        self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'])
        form_data = self.get_form_session_data()
        self.assertEqual(
            form_data.get('counties'), ['alameda', 'contracosta'])

    def test_logs_validation_errors_event(self):
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            response = self.client.fill_form(reverse('intake-apply'))
        assertInLogs(logs, 'application_errors')
        assertInLogs(
            logs, 'distinct_id=' + response.wsgi_request.visitor.get_uuid())

    def test_shows_error_messages_in_flash(self):
        response = self.client.fill_form(
            reverse('intake-apply'))
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
        for slug, county in County.objects.get_county_choices():
            self.assertContains(county_view, slug)
            self.assertIn(
                escape(county.description), county_view.rendered_content)

        applicant_id = self.client.session.get('applicant_id')
        self.assertIsNone(applicant_id)

    def test_anonymous_user_can_submit_county_selection(self):
        self.be_anonymous()
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            response = self.client.fill_form(
                reverse('intake-apply'),
                counties=['contracosta'],
                headers={'HTTP_USER_AGENT': 'tester'})
        self.assertRedirects(response, reverse('intake-county_application'))
        applicant_id = self.client.session.get('applicant_id')
        self.assertTrue(applicant_id)
        applicant = models.Applicant.objects.get(id=applicant_id)
        self.assertTrue(applicant)
        self.assertTrue(applicant.visitor_id)
        visitor = models.Visitor.objects.get(id=applicant.visitor_id)
        self.assertTrue(visitor)
        self.assertEqual(len(logs.output), 4)
        assertInLogsCount(logs, {
            'event_name=site_entered': 1,
            'event_name=page_viewed': 1,
            'event_name=application_started': 1,
            'event_name=application_page_complete': 1,
            'call_to_mixpanel': 4,
            'distinct_id=' + visitor.get_uuid(): 4,
        })
        assertInLogs(
            logs, 'user_agent', 'referrer', 'source', 'counties', 'contracosta'
        )

    def test_creates_applicant(self):
        response = self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'])
        self.assertTrue(response.wsgi_request.applicant.id)

    def test_create_applicant_with_existing_visitor_and_applicant(self):
        existing_applicant = factories.ApplicantFactory()
        self.set_session(visitor_id=existing_applicant.visitor.id)
        response = self.client.fill_form(
            reverse('intake-apply'), counties=['alameda', 'contracosta'])
        self.assertEqual(
            response.wsgi_request.applicant, existing_applicant)
