import logging
from datetime import timedelta
from unittest.mock import patch
from django.core.urlresolvers import reverse
from markupsafe import escape
from django.contrib.auth.models import User
from project.tests.assertions import assertInLogsCount
from user_accounts.models import Organization
from intake import models
from intake.tests.base_testcases import IntakeDataTestCase
from intake.tests import factories


class AppDetailFixturesBaseTestCase(IntakeDataTestCase):
    fixtures = [
        'counties', 'groups',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_2_submissions_to_ebclc',
        'mock_2_submissions_to_santa_clara_pubdef',
        'mock_1_submission_to_multiple_orgs', 'template_options'
    ]

    def get_page(self, submission):
        url = reverse(
            self.view_name, kwargs=dict(submission_id=submission.id))
        return self.client.get(url)


class TestApplicationDetail(AppDetailFixturesBaseTestCase):
    view_name = 'intake-app_detail'

    def assertHasDisplayData(self, response, submission):
        for field, value in submission.answers.items():
            if field in self.display_field_checks:
                escaped_value = escape(value)
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
        response = self.get_page(submission)
        self.assertEqual(response.context_data['submission'], submission)
        self.assertNotContains(response, escape('update-status-button'))

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_cant_see_app_detail_for_other_county(self, slack):
        self.be_ccpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertRedirects(response, reverse('user_accounts-profile'))
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
        transfer_action_url = escape(
            submission.get_transfer_action(response.wsgi_request)['url'])
        self.assertContains(response, transfer_action_url)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_ebclc_and_santa_clara_can_see_pref_pronouns(self, slack):
        ebclc = Organization.objects.get(slug='ebclc')
        santa_clara = Organization.objects.filter(
            slug__contains='santa_clara').first()
        self.be_user(
            User.objects.filter(profile__organization=ebclc).first())
        sub = models.FormSubmission.objects.filter(
            organizations=ebclc).first()
        response = self.get_page(sub)
        self.assertContains(
            response, escape(sub.answers.get('preferred_pronouns')))
        self.be_user(
            User.objects.filter(profile__organization=santa_clara).first())
        sub = models.FormSubmission.objects.filter(
            organizations=santa_clara).first()
        response = self.get_page(sub)
        self.assertContains(
            response, escape(sub.answers.get('preferred_pronouns')))

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_agency_user_can_see_case_printout_link(self, slack):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        printout_url = escape(
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
            response, escape(latest_status))

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_agency_user_can_only_see_latest_status_for_their_org(self, slack):
        user = self.be_apubdef_user()
        orgs = [
            Organization.objects.get(slug='a_pubdef'),
            Organization.objects.get(slug='cc_pubdef')
            ]
        submission = factories.FormSubmissionWithOrgsFactory(
            organizations=orgs)
        for org in orgs:
            updated_application = models.Application.objects.filter(
                organization=org, form_submission=submission).first()
            factories.StatusUpdateWithNotificationFactory.create(
                application=updated_application,
                author=org.profiles.first().user)
            updated_application.has_been_opened = True
            updated_application.save()
        statuses = models.StatusUpdate.objects.filter(
            application__form_submission=submission)
        latest_status = statuses.filter(
            application__organization=user.profile.organization,
        ).latest('updated')
        latest_status_date = statuses.latest('updated').updated
        even_later = latest_status_date + timedelta(days=3)
        other_status = statuses.exclude(
            application__organization=user.profile.organization,
        ).first()
        other_status.updated = even_later
        other_status.save()
        response = self.get_page(submission)
        other_logged_by = 'logged by ' + other_status.author.profile.name
        other_status_name = other_status.status_type.display_name
        this_status_logged_by = \
            'logged by ' + latest_status.author.profile.name
        this_status_name = latest_status.status_type.display_name
        self.assertContains(response, escape(this_status_name))
        self.assertContains(response, escape(this_status_logged_by))
        self.assertNotContains(response, escape(other_logged_by))
        if other_status_name not in this_status_name:
            self.assertNotContains(response, escape(other_status_name))

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_shows_new_if_no_status_updates(self, slack):
        user = self.be_ccpubdef_user()
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[user.profile.organization])
        response = self.get_page(submission)
        self.assertContains(response, 'New')

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_marks_apps_as_opened(self, slack):
        user = self.be_ccpubdef_user()
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[user.profile.organization])
        self.get_page(submission)
        application = submission.applications.filter(
            organization=user.profile.organization).first()
        self.assertTrue(application.has_been_opened)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_fires_expected_mixpanel_events(self, slack):
        user = self.be_ccpubdef_user()
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[user.profile.organization])
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.get_page(submission)
        assertInLogsCount(logs, {'event_name=app_opened': 1})
        assertInLogsCount(logs, {'event_name=user_app_opened': 1})


class TestAppDetailWithTransfers(AppDetailFixturesBaseTestCase):

    view_name = 'intake-app_detail'
    fixtures = AppDetailFixturesBaseTestCase.fixtures + [
        'mock_2_transfers'
    ]

    @patch('intake.notifications.slack_submissions_viewed.send')
    def check_that_outgoing_transfer_has_expected_info(self, slack):
        user = self.be_apubdef_user()
        outgoing_transfer = models.ApplicationTransfer.objects.filter(
            status_update__application__organization__profiles__user=user
        ).first()
        submission = outgoing_transfer.application.form_submission
        response = self.get_page(submission)
        expected_message = "Transferred to {} by {}".format(
            outgoing_transfer.new_application.organization.name,
            outgoing_transfer.status_update.author.profile.name)
        self.assertContains(response, escape(expected_message))
        self.assertContains(response, escape(outgoing_transfer.reason))
        self.assertNotContains(response, escape('update-status-button'))

    @patch('intake.notifications.slack_submissions_viewed.send')
    def check_that_incoming_transfer_has_expected_info(self, slack):
        user = User.objects.filter(profile__organization__slug='ebclc').first()
        self.be_user(user)
        incoming_transfer = models.ApplicationTransfer.objects.filter(
            new_application__organization__profiles__user=user).first()
        submission = incoming_transfer.new_application.form_submission
        response = self.get_page(submission)
        expected_message = "Transferred from {} by {}".format(
            incoming_transfer.status_update.application.organization.name,
            incoming_transfer.status_update.author.profile.name)
        self.assertContains(response, escape(expected_message))
        self.assertContains(response, escape(incoming_transfer.reason))

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_fires_expected_mixpanel_events(self, slack):
        user = self.be_ccpubdef_user()
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[user.profile.organization])
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.get_page(submission)
        assertInLogsCount(logs, {'event_name=app_opened': 1})
        assertInLogsCount(logs, {'event_name=user_app_opened': 1})


class TestApplicationHistory(AppDetailFixturesBaseTestCase):

    view_name = 'intake-app_history'

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_anonymous_user_is_redirected_to_login_history(self, slack):
        self.be_anonymous()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_accounts-login'), response.url)
        slack.assert_not_called()

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_logged_in_user_can_get_submission_display_history(self, slack):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.context_data['submission'], submission)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_staff_user_can_get_submission_display_history(self, slack):
        self.be_cfa_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.context_data['submission'], submission)
        self.assertNotContains(response, escape('update-status-button'))

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_cant_see_app_history_for_other_county(self, slack):
        self.be_ccpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertRedirects(response, reverse('user_accounts-profile'))
        slack.assert_not_called()

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_can_see_app_history_for_multi_county(self, slack):
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
            response, escape('Application History'))

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_can_only_see_own_status_updates_in_history(self, slack):
        user = self.be_apubdef_user()
        submission = self.combo_submissions[0]
        response = self.get_page(submission)
        status_updates = response.context_data['status_updates']
        for status_update in status_updates:
            self.assertEqual(
                status_update['organization_name'],
                user.profile.organization.name)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_shows_new_if_no_status_updates(self, slack):
        user = self.be_ccpubdef_user()
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[user.profile.organization])
        response = self.get_page(submission)
        self.assertContains(response, 'New')

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_marks_apps_as_opened(self, slack):
        user = self.be_ccpubdef_user()
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[user.profile.organization])
        self.get_page(submission)
        application = submission.applications.filter(
            organization=user.profile.organization).first()
        self.assertTrue(application.has_been_opened)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_fires_expected_mixpanel_events(self, slack):
        user = self.be_ccpubdef_user()
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[user.profile.organization])
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.get_page(submission)
        assertInLogsCount(logs, {'event_name=app_opened': 1})
        assertInLogsCount(logs, {'event_name=user_app_opened': 1})


class TestApplicationHistoryWithTransfers(AppDetailFixturesBaseTestCase):

    view_name = 'intake-app_history'
    fixtures = AppDetailFixturesBaseTestCase.fixtures + [
        'mock_2_transfers'
    ]

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_has_read_only_view_of_outgoing_transfer(self, slack):
        user = self.be_apubdef_user()
        outgoing_transfer = models.ApplicationTransfer.objects.filter(
            status_update__application__organization__profiles__user=user
        ).first()
        status_update = outgoing_transfer.status_update
        submission = \
            outgoing_transfer.status_update.application.form_submission
        response = self.get_page(submission)
        expected_display_data = [
            "{} at {}".format(
                status_update.author.profile.name,
                status_update.author.profile.organization.name),
            "Transferred to",
            outgoing_transfer.new_application.organization.name,
            outgoing_transfer.reason,
            status_update.notification.sent_message
        ]
        for expected_data in expected_display_data:
            self.assertContains(response, escape(expected_data))
        self.assertNotContains(response, escape('update-status-button'))

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_can_see_incoming_transfer_event(self, slack):
        user = User.objects.filter(profile__organization__slug='ebclc').first()
        self.be_user(user)
        incoming_transfer = models.ApplicationTransfer.objects.filter(
            new_application__organization__profiles__user=user).first()
        status_update = incoming_transfer.status_update
        submission = incoming_transfer.new_application.form_submission
        response = self.get_page(submission)
        expected_display_data = [
            "{} at {}".format(
                status_update.author.profile.name,
                status_update.author.profile.organization.name),
            "Transferred to",
            incoming_transfer.new_application.organization.name,
            incoming_transfer.reason,
            status_update.notification.sent_message
        ]
        for expected_data in expected_display_data:
            self.assertContains(response, escape(expected_data))

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_can_see_prior_status_updates_on_incoming_transfer(self, slack):
        user = User.objects.filter(profile__organization__slug='ebclc').first()
        self.be_user(user)
        incoming_transfer = models.ApplicationTransfer.objects.filter(
            new_application__organization__profiles__user=user).first()
        submission = incoming_transfer.new_application.form_submission
        response = self.get_page(submission)
        prior_updates = models.StatusUpdate.objects.filter(
            application__form_submission=submission,
            created__lt=incoming_transfer.status_update.created
        ).exclude(transfer=incoming_transfer)
        for status_update in prior_updates:
            expected_display_data = [
                "{} at {}".format(
                    status_update.author.profile.name,
                    status_update.author.profile.organization.name),
                status_update.status_type.display_name,
                status_update.notification.sent_message
            ]
            for expected_data in expected_display_data:
                self.assertContains(response, escape(expected_data))

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_fires_expected_mixpanel_events(self, slack):
        user = self.be_ccpubdef_user()
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[user.profile.organization])
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.get_page(submission)
        assertInLogsCount(logs, {'event_name=app_opened': 1})
        assertInLogsCount(logs, {'event_name=user_app_opened': 1})
