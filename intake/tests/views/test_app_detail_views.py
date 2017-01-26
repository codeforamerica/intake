from unittest.mock import patch
from django.core.urlresolvers import reverse
from django.utils import html as html_utils
from intake import models
from intake.tests.base_testcases import IntakeDataTestCase


class AppDetailAccessBaseTests(IntakeDataTestCase):
    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs', 'template_options'
        ]


class TestApplicationDetail(AppDetailAccessBaseTests):

    def get_page(self, submission):
        url = reverse(
            'intake-app_detail', kwargs=dict(submission_id=submission.id))
        return self.client.get(url)

    def assertHasDisplayData(self, response, submission):
        for field, value in submission.answers.items():
            if field in self.display_field_checks:
                escaped_value = html_utils.conditional_escape(value)
                self.assertContains(response, escaped_value)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_anonymous_user_is_redirected_to_login(self, slack):
        self.be_anonymous()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_accounts-login'), response.url)
        slack.assert_not_called()

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_logged_in_user_can_get_submission_display(self, slack):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.context_data['submission'], submission)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_staff_user_can_get_submission_display(self, slack):
        self.be_cfa_user()
        submission = self.a_pubdef_submissions[0]
        result = self.get_page(submission)
        self.assertEqual(result.context_data['submission'], submission)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_cant_see_app_detail_for_other_county(self, slack):
        self.be_ccpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertRedirects(response, reverse('intake-app_index'))
        slack.assert_not_called()

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_can_see_app_detail_for_multi_county(self, slack):
        self.be_apubdef_user()
        submission = self.combo_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.context_data['submission'], submission)

    @patch('intake.models.FillablePDF')
    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_with_pdf_redirected_to_pdf(self, slack, FillablePDF):
        self.be_sfpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        result = self.get_page(submission)
        self.assertRedirects(
            result,
            reverse(
                'intake-filled_pdf', kwargs=dict(submission_id=submission.id)),
            fetch_redirect_response=False)
        slack.assert_not_called()  # notification should be handled by pdf view
        FillablePDF.assert_not_called()

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_agency_user_can_see_display_form_content(self, slack):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertHasDisplayData(response, submission)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_agency_user_can_see_transfer_action_link(self, slack):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        transfer_action_url = html_utils.conditional_escape(
            submission.get_transfer_action(response.wsgi_request)['url'])
        self.assertContains(response, transfer_action_url)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_agency_user_can_see_case_printout_link(self, slack):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        printout_url = html_utils.conditional_escape(
            submission.get_case_printout_url())
        self.assertContains(response, printout_url)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_agency_user_can_see_latest_status(self, slack):
        user = self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        latest_status = models.StatusUpdate.objects.filter(
            application__organization=user.profile.organization,
            application__form_submission=submission
            ).latest('updated').status_type.display_name
        self.assertContains(
            response, html_utils.conditional_escape(latest_status))


class TestApplicationHistory(AppDetailAccessBaseTests):

    def get_page(self, submission):
        url = reverse(
            'intake-app_history', kwargs=dict(submission_id=submission.id))
        return self.client.get(url)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_anonymous_user_is_redirected_to_login(self, slack):
        self.be_anonymous()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_accounts-login'), response.url)
        slack.assert_not_called()

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_logged_in_user_can_get_submission_display(self, slack):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.context_data['submission'], submission)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_staff_user_can_get_submission_display(self, slack):
        self.be_cfa_user()
        submission = self.a_pubdef_submissions[0]
        result = self.get_page(submission)
        self.assertEqual(result.context_data['submission'], submission)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_cant_see_app_detail_for_other_county(self, slack):
        self.be_ccpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertRedirects(response, reverse('intake-app_index'))
        slack.assert_not_called()

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_can_see_app_detail_for_multi_county(self, slack):
        self.be_apubdef_user()
        submission = self.combo_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.context_data['submission'], submission)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_shows_app_history_in_title(self, slack):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertContains(
            response, html_utils.conditional_escape('Application History'))
