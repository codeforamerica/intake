from intake.tests.views.test_applicant_form_view_base \
    import ApplicantFormViewBaseTestCase
from django.urls import reverse
from intake.tests import factories, mock
from markupsafe import escape
from project.jinja2 import linkify


class TestThanksView(ApplicantFormViewBaseTestCase):
    view_name = 'intake-thanks'

    def test_redirects_to_apply_if_no_applicant(self):
        response = self.client.get(reverse(self.view_name))
        self.assertRedirects(response, reverse('intake-home'))

    def test_applicant_with_no_submission(self):
        # what really should this page be doing?
        applicant = factories.ApplicantFactory.create()
        self.set_session(applicant_id=applicant.id)
        response = self.client.get(reverse(self.view_name))
        self.assertRedirects(response, reverse('intake-home'))

    def test_applicant_with_submission(self):
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[self.cc_pubdef])
        self.set_session(applicant_id=submission.applicant_id)
        response = self.client.get(reverse(self.view_name))
        for org in submission.organizations.all():
            self.assertContains(response, escape(org.county.name))
            self.assertContains(response, escape(org.name))
            self.assertContains(
                response, linkify(org.long_confirmation_message))

    def test_clears_session_data(self):
        submission = factories.FormSubmissionWithOrgsFactory.create()
        self.set_session(visitor_id=submission.applicant.visitor.id)
        self.set_form_session_data(
            counties=['alameda', 'contracosta'],
            applicant=submission.applicant,
            **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers())
        )
        self.client.get(reverse(self.view_name))
        form_data = self.get_form_session_data()
        self.assertEqual(form_data, None)
        applicant_id = self.client.session.get('applicant_id', None)
        visitor_id = self.client.session.get('visitor_id', None)
        self.assertEqual(applicant_id, None)
        self.assertEqual(visitor_id, None)

    def test_shows_flash_messages(self):
        self.set_form_session_data(counties=['contracosta'])
        flash_messages = [
            "A flying horse is called a pegasus",
            "A horse with a horn is called a unicorn"]
        self.send_confirmations.return_value = flash_messages
        self.client.fill_form(
            reverse('intake-county_application'),
            follow=True,
            **mock.fake.cc_pubdef_answers())
        response = self.client.fill_form(
            reverse('intake-review'),
            follow=True,
            submit_action='approve_application'
        )
        for message in flash_messages:
            self.assertContains(
                response, escape(message))


class TestRAPSheetInstructionsView(ApplicantFormViewBaseTestCase):
    view_name = 'intake-rap_sheet'

    def test_works_without_applicant(self):
        response = self.client.get(reverse(self.view_name))
        self.assertEqual(response.status_code, 200)

    def test_applicant_with_no_submission(self):
        self.set_form_session_data()
        response = self.client.get(reverse(self.view_name))
        self.assertEqual(response.status_code, 200)

    def test_clears_session_data(self):
        submission = factories.FormSubmissionWithOrgsFactory.create()
        self.set_session(visitor_id=submission.applicant.visitor.id)
        self.set_form_session_data(
            counties=['alameda', 'contracosta'],
            applicant=submission.applicant,
            **mock.fake.a_pubdef_answers(
                **mock.fake.declaration_letter_answers())
        )
        self.client.get(reverse(self.view_name))
        form_data = self.get_form_session_data()
        self.assertEqual(form_data, None)
        applicant_id = self.client.session.get('applicant_id', None)
        visitor_id = self.client.session.get('visitor_id', None)
        self.assertEqual(applicant_id, None)
        self.assertEqual(visitor_id, None)

    def test_applicant_with_submission(self):
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[self.ebclc, self.cc_pubdef])
        self.set_session(applicant_id=submission.applicant_id)
        response = self.client.get(reverse(self.view_name))
        for org in submission.organizations.all():
            self.assertContains(response, escape(org.county.name))
            self.assertContains(response, escape(org.name))
            self.assertContains(
                response, linkify(org.long_confirmation_message))

    def test_shows_flash_messages(self):
        self.set_form_session_data(counties=['alameda'])
        flash_messages = [
            "A flying horse is called a pegasus",
            "A horse with a horn is called a unicorn"]
        self.send_confirmations.return_value = flash_messages
        self.client.fill_form(
            reverse('intake-county_application'),
            follow=True,
            **mock.fake.ebclc_answers())
        response = self.client.fill_form(
            reverse('intake-review'),
            follow=True,
            submit_action='approve_application'
        )
        for message in flash_messages:
            self.assertContains(
                response, escape(message))
