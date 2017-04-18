from django.test import TestCase
from user_accounts.tests import clients
from project.fixtures_index import ESSENTIAL_DATA_FIXTURES
from django.core.urlresolvers import reverse
from intake.views.applicant_form_view_base import ApplicantFormViewBase
from django.http.request import QueryDict
from intake import utils


class TestSelectCountyView(TestCase):

    client_class = clients.CsrfClient
    fixtures = ESSENTIAL_DATA_FIXTURES

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
        pass

    def test_no_county_confirmation_returns_and_shows_error(self):
        pass

    def test_no_counties_selected_returns_error(self):
        pass

    def test_logs_page_complete_event(self):
        pass

    def test_saves_form_data_to_session(self):
        pass

    def test_logs_validation_errors_event(self):
        pass

    def test_shows_error_messages_in_flash(self):
        pass

    def test_get_page_shows_existing_data(self):
        pass
