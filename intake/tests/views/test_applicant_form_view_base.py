from unittest.mock import patch, Mock
from project.fixtures_index import ESSENTIAL_DATA_FIXTURES
from user_accounts.tests.base_testcases import AuthIntegrationTestCase
from intake.views.applicant_form_view_base import ApplicantFormViewBase
from intake import models


class ApplicantFormViewBaseTestCase(AuthIntegrationTestCase):
    fixtures = ESSENTIAL_DATA_FIXTURES

    def set_form_session_data(self, **data):
        querydictifiable_data = {}
        for key, value in data.items():
            if not isinstance(value, list):
                value = [value]
            querydictifiable_data[key] = value
        self.set_session(**{
            ApplicantFormViewBase.session_key: querydictifiable_data})


class TestApplicantFormViewBase(ApplicantFormViewBaseTestCase):

    def redirects_if_empty_counties_in_session(self):
        mock_view_instance = Mock(session_data={'counties': []})
        result = ApplicantFormViewBase.check_for_session_based_redirects(
            mock_view_instance)
        import ipdb; ipdb.set_trace()

    def redirects_if_no_counties_in_session(self):
        mock_view_instance = Mock(session_data={})
        result = ApplicantFormViewBase.check_for_session_based_redirects(
            mock_view_instance)

    def doesnt_redirect_if_has_counties_in_session(self):
        mock_view_instance = Mock(
            session_data={'counties': ['alameda', 'contracosta']})
        result = ApplicantFormViewBase.check_for_session_based_redirects(
            mock_view_instance)

    @patch('intake.models.county.Count.get_receiving_agency')
    def test_get_receiving_organizations_if_no_attribute(self, get_agency):
        counties = models.County.objects.all()[:2]
        orgs = [
            models.Organization.objects.filter(county_id=county.id).first()
            for county in counties]
        get_agency.side_effect = orgs
        mock_view_instance = Mock(
            receiving_organizations=None, counties=counties)
        results = ApplicantFormViewBase.get_receiving_organizations(
            mock_view_instance, Mock())
        self.assertEqual(get_agency.call_count, 2)
        self.assertListEqual(orgs, results)
        self.assertListEqual(
            orgs, mock_view_instance.receiving_organization)

    @patch('intake.models.county.Count.get_receiving_agency')
    def test_get_receiving_organizations_if_exists(self, get_agency):
        counties = models.County.objects.all()[:2]
        orgs = [
            models.Organization.objects.filter(county_id=county.id).first()
            for county in counties]
        get_agency.side_effect = orgs
        mock_view_instance = Mock(
            receiving_organizations=orgs, counties=counties)
        results = ApplicantFormViewBase.get_receiving_organizations(
            mock_view_instance, Mock())
        self.assertEqual(get_agency.call_count, 0)
        self.assertListEqual(orgs, results)
        self.assertListEqual(
            orgs, mock_view_instance.receiving_organization)

    def test_finalize_application_actions(self):
        pass
