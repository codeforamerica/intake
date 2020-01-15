import logging
from django.urls import reverse
from formation import fields
from markupsafe import escape
from unittest.mock import patch
from intake import models
from intake.tests import mock
from intake.tests.views.test_applicant_form_view_base \
    import ApplicantFormViewBaseTestCase
from project.tests.assertions import assertInLogsCount


# these actually probably work independent of the existing county application
# form answers in session
# but all of these tests ensure the session has expected answers


class TestWriteDeclarationLetterView(ApplicantFormViewBaseTestCase):
    view_name = 'intake-write_letter'
    fixtures = ['counties', 'organizations', 'groups', 'mock_profiles']

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
            response, "You are applying for help in Alameda.")

    def test_logs_page_complete_event(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers())
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.client.fill_form(
                reverse(self.view_name),
                **mock.fake.declaration_letter_answers())
        assertInLogsCount(
            logs, {
                'event_name=application_page_complete': 1,
                'event_name=application_started': 0,
                'event_name=application_submitted': 0,
                'event_name=application_errors': 0,
                })

    def test_saves_form_data_to_session(self):
        answers = mock.fake.declaration_letter_answers()
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers())
        self.client.fill_form(
            reverse(self.view_name), **answers)
        form_data = self.get_form_session_data()
        for key, value in answers.items():
            self.assertEqual(form_data[key], [value])

    def test_logs_validation_errors_event(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers())
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.client.fill_form(
                reverse(self.view_name),
                **mock.fake.declaration_letter_answers(
                    declaration_letter_intro=''))
        assertInLogsCount(
            logs, {
                'event_name=application_page_complete': 0,
                'event_name=application_started': 0,
                'event_name=application_submitted': 0,
                'event_name=application_errors': 1,
                })

    @patch(
        'intake.services.submissions.send_confirmation_notifications')
    def test_that_declaration_letter_properly_escapes_html(self, *patches):
        # this is a regression test to ensure that html cannot be injected
        # into declaration letters, and that we don't overescape
        mock_letter = mock.fake.declaration_letter_answers()
        mock_answers = mock.fake.a_pubdef_answers(
            first_name="foo", last_name="e2f79c23fcc04ed78fa1ea29f12a0323")
        html_string = '<img src="omg.gif"> O\'Brien'
        escaped_name = escape('O\'Brien')
        for field in mock_letter:
            mock_letter[field] = html_string
        self.be_anonymous()
        self.client.fill_form(
            reverse('intake-apply'), counties=['alameda'], follow=True)
        self.client.fill_form(
            reverse('intake-county_application'), follow=True, **mock_answers)
        response = self.client.fill_form(
            reverse('intake-write_letter'), follow=True, **mock_letter)
        # check that the html is not in the review page
        self.assertNotContains(response, html_string)
        self.assertContains(response, escaped_name)
        response = self.client.fill_form(
            reverse('intake-review_letter'),
            submit_action="approve_letter")

        # check that the html is not in the app detail page
        self.be_apubdef_user()
        submission = models.FormSubmission.objects.filter(
            last_name="e2f79c23fcc04ed78fa1ea29f12a0323").first()
        response = self.client.get(
            reverse(
                'intake-app_detail', kwargs=dict(submission_id=submission.id)))
        self.assertNotContains(response, html_string)
        self.assertContains(response, escaped_name)


class TestReviewDeclarationLetterView(ApplicantFormViewBaseTestCase):
    view_name = 'intake-review_letter'

    def test_shows_counties_where_applying(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers()))
        response = self.client.get(reverse(self.view_name))
        self.assertContains(
            response, "You are applying for help in Alameda.")

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

    def test_logs_page_complete_event(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers()))
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.client.fill_form(
                reverse(self.view_name), submit_action='approve_letter')
        assertInLogsCount(
            logs, {
                'event_name=application_page_complete': 1,
                'event_name=application_started': 0,
                'event_name=application_submitted': 1,
                'event_name=application_errors': 0,
                })

    def test_saves_form_data_to_session(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers()))
        self.client.fill_form(
            reverse(self.view_name), submit_action='approve_letter')
        form_data = self.get_form_session_data()
        self.assertEqual(form_data['submit_action'], ['approve_letter'])

    def test_logs_validation_errors_event(self):
        self.set_form_session_data(
            counties=['alameda'], **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers()))
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.client.fill_form(
                reverse(self.view_name), submit_action='invalid_option')
        assertInLogsCount(
            logs, {
                'event_name=application_page_complete': 0,
                'event_name=application_started': 0,
                'event_name=application_submitted': 0,
                'event_name=application_errors': 1,
                })
