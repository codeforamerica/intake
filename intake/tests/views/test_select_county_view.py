from django.test import TestCase
from user_accounts.tests import clients
from project.fixtures_index import ESSENTIAL_DATA_FIXTURES
from django.core.urlresolvers import reverse
from intake.views.applicant_form_view_base import ApplicantFormViewBase


class TestSelectCountyView(TestCase):

    client_class = clients.CsrfClient
    fixtures = ESSENTIAL_DATA_FIXTURES

    def test_county_selection_saved_to_session(self):
        self.client.fill_form(
            reverse('intake-apply'), counties=['a_pubdef', 'cc_pubdef'],
            confirm_county_selection='yes')
        form_data = self.client.session.get(ApplicantFormViewBase.session_key)
        self.assertListEqual(['a_pubdef', 'cc_pubdef'], form_data['counties'])
