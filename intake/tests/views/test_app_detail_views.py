import logging
from datetime import timedelta
from unittest.mock import patch
from django.urls import reverse
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

    def test_anonymous_user_is_redirected_to_login(self):
        self.be_anonymous()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_accounts-login'), response.url)

    def test_logged_in_user_can_get_submission_display(self):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.context_data['submission'], submission)

    def test_staff_user_can_get_submission_display(self):
        self.be_cfa_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.context_data['submission'], submission)
        self.assertNotContains(response, escape('update-status-button'))

    def test_user_cant_see_app_detail_for_other_county(self):
        self.be_ccpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertRedirects(response, reverse('user_accounts-profile'))

    def test_user_can_see_app_detail_for_multi_county(self):
        self.be_apubdef_user()
        submission = self.combo_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.context_data['submission'], submission)

    def test_agency_user_can_see_display_form_content(self):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertHasDisplayData(response, submission)

    def test_user_with_pdf_can_see_pdf_link(self):
        self.be_sfpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertContains(response, submission.get_filled_pdf_url())

    def test_user_without_pdf_cant_see_pdf_link(self):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertNotContains(response, submission.get_filled_pdf_url())

    def test_agency_user_can_see_transfer_action_link(self):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        transfer_action_url = escape(
            submission.get_transfer_action(response.wsgi_request)['url'])
        self.assertContains(response, transfer_action_url)

    def test_ebclc_and_santa_clara_can_see_pref_pronouns(self):
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

    def test_agency_user_can_see_case_printout_link(self):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        printout_url = escape(
            submission.get_case_printout_url())
        self.assertContains(response, printout_url)

    def test_agency_user_can_see_latest_status(self):
        user = self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        latest_status = models.StatusUpdate.objects.filter(
            application__organization=user.profile.organization,
            application__form_submission=submission
        ).latest('updated').status_type.display_name
        self.assertContains(
            response, escape(latest_status))

    def test_agency_user_can_only_see_latest_status_for_their_org(self):
        user = self.be_apubdef_user()
        other_org = Organization.objects.get(slug='cc_pubdef')
        submission = factories.FormSubmissionWithOrgsFactory(
            organizations=[user.profile.organization, other_org])

        # make a status notification for the other org
        other_app = models.Application.objects.filter(
                organization=other_org, form_submission=submission).first()
        other_status_type = models.StatusType.objects.get(slug='court-date')
        factories.StatusUpdateWithNotificationFactory.create(
            status_type=other_status_type,
            application=other_app,
            author=other_org.profiles.first().user)
        other_app.has_been_opened = True
        other_app.save()

        # make a status notification for tis org
        this_status_type = models.StatusType.objects.get(slug='eligible')
        this_app = models.Application.objects.filter(
            organization__profiles__user=user,
            form_submission=submission).first()
        factories.StatusUpdateWithNotificationFactory.create(
            status_type=this_status_type,
            application=this_app,
            author=user)
        this_app.has_been_opened = True
        this_app.save()

        # set the other status notification date to be later than this one
        statuses = models.StatusUpdate.objects.filter(
            application__form_submission=submission)
        this_status = statuses.filter(
            application__organization=user.profile.organization,
        ).latest('updated')
        this_status_date = statuses.latest('updated').updated
        even_later = this_status_date + timedelta(days=3)
        other_status = statuses.exclude(
            application__organization=user.profile.organization,
        ).first()
        other_status.updated = even_later
        other_status.save()

        response = self.get_page(submission)
        other_logged_by = 'logged by ' + other_status.author.profile.name
        other_status_name = other_status.status_type.display_name
        this_status_logged_by = \
            'logged by ' + this_status.author.profile.name
        this_status_name = this_status.status_type.display_name
        self.assertContains(response, escape(this_status_name))
        self.assertContains(response, escape(this_status_logged_by))
        self.assertNotContains(response, escape(other_logged_by))
        self.assertNotContains(response, escape(other_status_name))

    def test_shows_new_if_no_status_updates(self):
        user = self.be_ccpubdef_user()
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[user.profile.organization])
        response = self.get_page(submission)
        self.assertContains(response, 'New')

    def test_marks_apps_as_opened(self):
        user = self.be_ccpubdef_user()
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[user.profile.organization])
        self.get_page(submission)
        application = submission.applications.filter(
            organization=user.profile.organization).first()
        self.assertTrue(application.has_been_opened)

    def test_fires_expected_mixpanel_events(self):
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

    def check_that_outgoing_transfer_has_expected_info(self):
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

    def check_that_incoming_transfer_has_expected_info(self):
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

    def test_fires_expected_mixpanel_events(self):
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

    def test_anonymous_user_is_redirected_to_login_history(self):
        self.be_anonymous()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_accounts-login'), response.url)

    def test_logged_in_user_can_get_submission_display_history(self):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.context_data['submission'], submission)

    def test_staff_user_can_get_submission_display_history(self):
        self.be_cfa_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.context_data['submission'], submission)
        self.assertNotContains(response, escape('update-status-button'))

    def test_user_cant_see_app_history_for_other_county(self):
        self.be_ccpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertRedirects(response, reverse('user_accounts-profile'))

    def test_user_can_see_app_history_for_multi_county(self):
        self.be_apubdef_user()
        submission = self.combo_submissions[0]
        response = self.get_page(submission)
        self.assertEqual(response.context_data['submission'], submission)

    def test_shows_app_history_in_title(self):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_page(submission)
        self.assertContains(
            response, escape('Application History'))

    def test_user_can_only_see_own_status_updates_in_history(self):
        user = self.be_apubdef_user()
        submission = self.combo_submissions[0]
        response = self.get_page(submission)
        status_updates = response.context_data['status_updates']
        for status_update in status_updates:
            self.assertEqual(
                status_update['organization_name'],
                user.profile.organization.name)

    def test_shows_new_if_no_status_updates(self):
        user = self.be_ccpubdef_user()
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[user.profile.organization])
        response = self.get_page(submission)
        self.assertContains(response, 'New')

    def test_marks_apps_as_opened(self):
        user = self.be_ccpubdef_user()
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[user.profile.organization])
        self.get_page(submission)
        application = submission.applications.filter(
            organization=user.profile.organization).first()
        self.assertTrue(application.has_been_opened)

    def test_fires_expected_mixpanel_events(self):
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

    def test_has_read_only_view_of_outgoing_transfer(self):
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

    def test_can_see_incoming_transfer_event(self):
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

    def test_can_see_prior_status_updates_on_incoming_transfer(self):
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

    def test_fires_expected_mixpanel_events(self):
        user = self.be_ccpubdef_user()
        submission = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[user.profile.organization])
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            self.get_page(submission)
        assertInLogsCount(logs, {'event_name=app_opened': 1})
        assertInLogsCount(logs, {'event_name=user_app_opened': 1})
