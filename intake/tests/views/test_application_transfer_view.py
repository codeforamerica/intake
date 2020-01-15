"""
- EBCLC can see the reason
- EBCLC can see the transfer in the app bundle
- EBCLC can see the transfer in the app history
"""
from unittest.mock import patch
from intake import models
import intake.services.transfers_service as TransferService
from user_accounts.models import Organization
from intake.tests.base_testcases import IntakeDataTestCase
from django.urls import reverse
from markupsafe import escape
from intake.views.base_views import NOT_ALLOWED_MESSAGE


class TestApplicationTransferView(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations',
        'groups',
        'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_1_bundle_to_a_pubdef',
        'template_options'
    ]

    def post(self, **custom_inputs):
        inputs = dict(
            author=self.from_org.profiles.first().user.pk,
            to_organization=self.to_org.pk,
            reason="because of subspace interference",
            sent_message="we are sending you to the other place")
        inputs.update(**custom_inputs)
        return self.client.fill_form(
            self.url, **inputs)

    def setUp(self):
        self.from_org = Organization.objects.get(slug='a_pubdef')
        self.to_org = Organization.objects.get(slug='ebclc')
        self.sub = models.FormSubmission.objects.filter(
            organizations=self.from_org).first()
        self.sub.answers['contact_preferences'] = [
            'prefers_email',
            'prefers_sms']
        self.sub.save()
        self.bundle = models.ApplicationBundle.objects.filter(
            organization=self.from_org).first()
        self.url = reverse(
            'intake-transfer_application',
            kwargs=dict(submission_id=self.sub.id))
        self.bundle_url = reverse(
            'intake-app_bundle_detail', kwargs=dict(bundle_id=self.bundle.id))
        self.detail_url = reverse(
            'intake-app_detail', kwargs=dict(submission_id=self.sub.id))

    @patch('intake.notifications.send_applicant_notification')
    def test_can_transfer_successfully(self, front):
        user = self.be_apubdef_user()
        self.assertEqual(
            0,
            models.ApplicationTransfer.objects.filter(
                new_application__form_submission_id=self.sub.id
            ).distinct().count())
        # perform the transfer
        response = self.post()
        # check the response
        self.assertRedirects(
            response, reverse('intake-app_index'),
            fetch_redirect_response=False)
        # check for resulting database objects
        transfers = models.ApplicationTransfer.objects.filter(
            new_application__form_submission_id=self.sub.id).distinct()
        self.assertEqual(transfers.count(), 1)
        transfer = transfers.first()
        self.assertEqual(transfer.new_application.organization, self.to_org)
        self.assertEqual(
            transfer.status_update.application.organization, self.from_org)
        self.assertEqual(transfer.status_update.author, user)
        self.assertEqual(transfer.reason, "because of subspace interference")
        sub_orgs = list(self.sub.organizations.all())
        self.assertIn(self.from_org, sub_orgs)
        self.assertIn(self.to_org, sub_orgs)
        self.assertTrue(transfer.status_update.application.was_transferred_out)
        self.assertTrue(transfer.status_update.notification)
        notification = transfer.status_update.notification
        self.assertTrue(transfer.status_update.notification.contact_info)
        sub = transfer.status_update.application.form_submission
        intro, default_body = \
            TransferService.render_application_transfer_message(
                form_submission=sub,
                author=user,
                to_organization=self.to_org,
                from_organization=self.from_org)
        expected_base_message = "\n\n".join([intro, default_body])
        expected_sent_message = "\n\n".join(
            [intro, "we are sending you to the other place"])
        self.assertEqual(notification.base_message, expected_base_message)
        self.assertEqual(notification.sent_message, expected_sent_message)
        self.assertDictEqual(
            notification.contact_info, sub.get_usable_contact_info())
        self.assertEqual(len(front.mock_calls), 1)
        front.assert_called_once_with(
            notification.contact_info, expected_sent_message,
            subject="Update from Clear My Record", sender_profile=user.profile)

    def test_sees_expected_message(self):
        user = self.be_apubdef_user()
        response = self.client.get(self.url)
        expected_intro, expected_body = \
            TransferService.render_application_transfer_message(
                form_submission=self.sub,
                author=user,
                to_organization=self.to_org,
                from_organization=self.from_org)
        self.assertContains(response, escape(expected_intro))
        self.assertContains(response, escape(expected_body))
        self.assertIn(self.to_org.name, expected_body)
        self.assertIn(self.from_org.name, expected_intro)
        self.assertIn(user.profile.name, expected_intro)
        self.assertContains(response, 'following message will be')
        self.assertContains(response, 'to the applicant')

    @patch('intake.notifications.send_applicant_notification')
    def test_from_bundle_is_redirected_back_to_bundle(self, front):
        self.be_apubdef_user()
        response = self.post(next_url=self.bundle_url)
        self.assertRedirects(
            response, self.bundle_url, fetch_redirect_response=False)
        response = self.client.get(response.url)
        # we still show the application in the bundle, we do not remove it from
        # the bundle
        self.assertContains(
            response,
            'data-submission-id="formsubmission-{}"'.format(self.sub.id))

    @patch('intake.notifications.send_applicant_notification')
    def test_from_detail_transfered_back_to_index(self, front):
        self.be_apubdef_user()
        response = self.post()
        self.assertRedirects(response, reverse('intake-app_index'))

    def test_org_users_without_transfers_are_redirected_to_profile(self):
        self.be_ccpubdef_user()
        response = self.client.get(self.url)
        self.assertRedirects(
            response, reverse('user_accounts-profile'),
            fetch_redirect_response=False)
        index = self.client.get(response.url)
        self.assertContains(index, escape(NOT_ALLOWED_MESSAGE))

    def test_anon_user_redirected_to_login(self):
        self.be_anonymous()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_accounts-login'), response.url)

    def test_cfa_user_redirected_to_profile(self):
        self.be_cfa_user()
        response = self.client.get(self.url)
        self.assertRedirects(
            response, reverse('user_accounts-profile'),
            fetch_redirect_response=False)
        index = self.client.get(response.url)
        self.assertContains(index, escape(NOT_ALLOWED_MESSAGE))

    def test_monitor_user_redirected_to_profile(self):
        self.be_monitor_user()
        response = self.client.get(self.url)
        self.assertRedirects(
            response, reverse('user_accounts-profile'),
            fetch_redirect_response=False)
