from intake.tests.base_testcases import IntakeDataTestCase
from unittest.mock import patch
from intake.tests import mock
from intake import models
from django.core.urlresolvers import reverse
from formation.field_types import YES
from intake.views import county_application_view

"""
    This is formerly test_application_form_views.py; it was renamed after all
    tests mapped to specific named views were pruned or migrated to the
    most appropriate test file (for clarity). The ultimate goal is to replace
    these tests with behave tests that mirror user behavior, but the tests that
    remain in this file are important to preserve until that time / serve as
    guideposts for eventual integration test direction.
"""


class TestFullCountyApplicationSequence(IntakeDataTestCase):

    @patch('intake.models.pdfs.get_parser')
    @patch('intake.services.submissions.send_confirmation_notifications')
    @patch(
        'intake.views.session_view_base.notifications'
        '.slack_new_submission.send')
    def test_anonymous_user_can_fill_out_app_and_reach_thanks_page(
            self, slack, send_confirmation, get_parser):
        get_parser.return_value.fill_pdf.return_value = b'a pdf'
        self.be_anonymous()
        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=['sanfrancisco'],
            confirm_county_selection=YES)
        self.assertRedirects(result, reverse('intake-county_application'))
        result = self.client.fill_form(
            reverse('intake-county_application'),
            **mock.fake.sf_county_form_answers())
        self.assertRedirects(
            result, reverse('intake-thanks'), fetch_redirect_response=False)
        thanks_page = self.client.get(result.url)
        filled_pdf = models.FilledPDF.objects.first()
        self.assertTrue(filled_pdf)
        self.assertTrue(filled_pdf.pdf)
        self.assertNotEqual(filled_pdf.pdf.size, 0)
        submission = models.FormSubmission.objects.order_by('-pk').first()
        self.assertEqual(filled_pdf.submission, submission)
        organization = submission.organizations.first()
        self.assertEqual(filled_pdf.original_pdf, organization.pdfs.first())
        self.assertContains(thanks_page, "Thank")
        self.assertEqual(len(slack.mock_calls), 1)
        send_confirmation.assert_called_once_with(submission)
        form_data = self.client.session.get('form_in_progress')
        self.assertFalse(form_data)

    @patch('intake.models.pdfs.get_parser')
    @patch('intake.services.submissions.send_confirmation_notifications')
    @patch('intake.notifications.slack_new_submission.send')
    def test_apply_to_sf_with_name_only(
            self, slack, send_confirmation, get_parser):
        get_parser.return_value.fill_pdf.return_value = b'a pdf'
        self.be_anonymous()
        response = self.client.fill_form(
            reverse('intake-apply'),
            counties=['sanfrancisco'],
            confirm_county_selection=YES,
            follow=True
        )
        # this should raise warnings
        response = self.client.fill_form(
            reverse('intake-county_application'),
            first_name="Foo",
            last_name="Bar",
            consent_to_represent='yes',
            understands_limits='yes',
        )
        self.assertRedirects(
            response, reverse('intake-confirm'), fetch_redirect_response=False)
        response = self.client.get(response.url)
        self.assertContains(response, "Foo")
        self.assertContains(response, "Bar")
        self.assertContains(
            response, fields.AddressField.is_recommended_error_message)
        self.assertContains(
            response,
            fields.SocialSecurityNumberField.is_recommended_error_message)
        self.assertContains(
            response, fields.DateOfBirthField.is_recommended_error_message)
        self.assertContains(
            response, str(county_application_view.WARNING_FLASH_MESSAGE))
        slack.assert_not_called()
        response = self.client.fill_form(
            reverse('intake-confirm'),
            first_name="Foo",
            last_name="Bar",
            consent_to_represent='yes',
            understands_limits='yes',
            follow=True
        )
        submission = models.FormSubmission.objects.filter(
            answers__first_name="Foo",
            answers__last_name="Bar").first()
        self.assertEqual(response.wsgi_request.path, reverse('intake-thanks'))
        self.assertEqual(len(slack.mock_calls), 1)
        send_confirmation.assert_called_once_with(submission)
