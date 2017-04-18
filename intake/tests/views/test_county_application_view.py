from intake.tests.views.test_applicant_form_view_base \
    import ApplicantFormViewBaseTestCase
from django.core.urlresolvers import reverse


class TestCountyApplicationNoWarningsView(ApplicantFormViewBaseTestCase):

    def test_with_no_applicant(self):
        pass

    def test_redirects_if_no_counties_in_session(self):
        response = self.client.get(reverse('intake-county_application'))
        self.assertRedirects(response, reverse('intake-apply'))

    def test_can_get_form_for_counties(self):
        self.set_form_session_data(counties=['alameda', 'contracosta'])
        response = self.client.get(reverse('intake-county_application'))
        self.assertEqual(response.status_code, 200)
        form = response.context_data['form']
        self.assertFalse(form.is_bound())
        for key in form.get_field_keys():
            self.assertContains(response, key)

    def test_can_get_form_filled_with_existing_data(self):
        self.set_form_session_data(
            counties=['alameda', 'contracosta'],
            first_name='Seven', middle_name='of', last_name='Nine')
        response = self.client.get(reverse('intake-county_application'))
        self.assertEqual(response.status_code, 200)
        form = response.context_data['form']
        self.assertTrue(form.is_bound())
        self.assertContains(response, 'Seven')
        self.assertContains(response, 'Nine')

    def test_needs_letter_post_redirects_to_write_letter_page(self):
        pass

    def test_successful_post_redirects_to_thanks_page(self):
        pass

    def test_needs_rap_sheet_redirects_to_rap_sheet_page(self):
        pass

    def test_validation_warnings(self):
        pass

    def test_invalid_post_shows_errors(self):
        pass

    def test_shows_counties_where_applying(self):
        pass

    def test_logs_page_complete_event(self):
        pass

    def test_saves_form_data_to_session(self):
        pass


class TestCountyApplicationView(TestCountyApplicationNoWarningsView):

    def test_validation_warnings(self):
        pass
