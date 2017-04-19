from unittest.mock import patch
from intake.tests.views.test_applicant_form_view_base \
    import ApplicantFormViewBaseTestCase
from django.core.urlresolvers import reverse
from intake.tests import mock
from formation import fields
from markupsafe import escape

# these actually probably work independent of the existing county application
# form answers in session
# but all of these tests ensure the session has expected answers


class TestWriteDeclarationLetterView(ApplicantFormViewBaseTestCase):
    view_name = 'intake-write_letter'

    def test_renders_declaration_letter_form(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers())
        response = self.client.get(reverse(self.view_name))
        form = response.context_data['form']
        keys = form.get_field_keys()
        for key in keys:
            self.assertContains(response, key)

    def test_with_no_applicant(self):
        self.set_form_session_data(
            counties=['alameda'], create_applicant=False)
        response = self.client.get(reverse(self.view_name))
        self.assertRedirects(response, reverse('intake-apply'))

    def test_applicant_with_no_counties(self):
        self.set_form_session_data(
            counties=[], **mock.fake.a_pubdef_answers())
        response = self.client.get(reverse(self.view_name))
        self.assertRedirects(response, reverse('intake-apply'))

    def test_get_displays_existing_answers(self):
        existing = mock.fake.declaration_letter_answers()
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers(**existing))
        response = self.client.get(reverse(self.view_name))
        for text in existing.values():
            self.assertContains(response, escape(text))

    def test_post_redirects_to_letter_review_page(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers())
        response = self.client.fill_form(
            reverse(self.view_name), **mock.fake.declaration_letter_answers())
        self.assertRedirects(response, reverse('intake-review_letter'))

    def test_invalid_post_shows_errors(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers())
        response = self.client.fill_form(
            reverse(self.view_name), **mock.fake.declaration_letter_answers(
                declaration_letter_intro=''))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, fields.DeclarationLetterIntro.is_required_error_message)

    def test_shows_counties_where_applying(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers())
        response = self.client.get(reverse(self.view_name))
        self.assertContains(
            response, "You are applying for help in Alameda County.")

    @patch('intake.services.events_service.log_form_page_complete')
    def test_logs_page_complete_event(self, event_log):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers())
        self.client.fill_form(
            reverse(self.view_name), **mock.fake.declaration_letter_answers())
        self.assertEqual(event_log.call_count, 1)

    def test_saves_form_data_to_session(self):
        answers = mock.fake.declaration_letter_answers()
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers())
        self.client.fill_form(
            reverse(self.view_name), **answers)
        form_data = self.get_form_session_data()
        for key, value in answers.items():
            self.assertEqual(form_data[key], [value])

    @patch('intake.services.events_service.log_form_validation_errors')
    def test_logs_validation_errors_event(self, event_log):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers())
        self.client.fill_form(
            reverse(self.view_name), **mock.fake.declaration_letter_answers(
                declaration_letter_intro=''))
        self.assertEqual(event_log.call_count, 1)


class TestReviewDeclarationLetterView(ApplicantFormViewBaseTestCase):
    view_name = 'intake-review_letter'

    def test_shows_counties_where_applying(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers()))
        response = self.client.get(reverse(self.view_name))
        self.assertContains(
            response, "You are applying for help in Alameda County.")

    def test_with_no_applicant(self):
        self.set_form_session_data(
            counties=['alameda'], create_applicant=False)
        response = self.client.get(reverse(self.view_name))
        self.assertRedirects(response, reverse('intake-apply'))

    def test_applicant_with_no_counties(self):
        self.set_form_session_data(
            counties=[], **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers()))
        response = self.client.get(reverse(self.view_name))
        self.assertRedirects(response, reverse('intake-apply'))

    def test_displays_existing_letter_data(self):
        existing = mock.fake.declaration_letter_answers()
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers(**existing))
        response = self.client.get(reverse(self.view_name))
        for text in existing.values():
            self.assertContains(response, escape(text))

    def test_approve_redirects_to_thanks_page(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers()))
        response = self.client.fill_form(
            reverse(self.view_name), submit_action='approve_letter')
        self.assertRedirects(response, reverse('intake-thanks'))

    def test_edit_redirects_to_write_letter_page(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers()))
        response = self.client.fill_form(
            reverse(self.view_name), submit_action='edit_letter')
        self.assertRedirects(response, reverse('intake-write_letter'))

    def test_invalid_post_returns_same_page(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers()))
        response = self.client.fill_form(
            reverse(self.view_name), submit_action='invalid_option')
        self.assertEqual(response.status_code, 200)

    @patch('intake.services.events_service.log_form_page_complete')
    def test_logs_page_complete_event(self, event_log):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers()))
        self.client.fill_form(
            reverse(self.view_name), submit_action='approve_letter')
        self.assertEqual(event_log.call_count, 1)

    def test_saves_form_data_to_session(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers()))
        self.client.fill_form(
            reverse(self.view_name), submit_action='approve_letter')
        form_data = self.get_form_session_data()
        self.assertEqual(form_data['submit_action'], ['approve_letter'])

    @patch('intake.services.events_service.log_form_validation_errors')
    def test_logs_validation_errors_event(self, event_log):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers()))
        self.client.fill_form(
            reverse(self.view_name), submit_action='invalid_option')
        self.assertEqual(event_log.call_count, 1)
