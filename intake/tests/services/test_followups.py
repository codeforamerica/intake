import logging
from django.test import TestCase
import intake.services.followups as FollowupsService
from intake.tests import factories
from intake.tests.mock import get_old_date, get_newer_date
from intake.tests.mock_org_answers import get_answers_for_orgs
from intake.tests.base_testcases import ExternalNotificationsPatchTestCase
from project.fixtures_index import (
    ESSENTIAL_DATA_FIXTURES,
    MOCK_USER_ACCOUNT_FIXTURES)
from user_accounts.models import Organization
from project.tests.assertions import assertInLogsCount

"""
Each function in intake.services.followups corresponds to a TestCase in this
file.
"""


class TestGetSubmissionsDueForFollowups(TestCase):
    fixtures = ESSENTIAL_DATA_FIXTURES + MOCK_USER_ACCOUNT_FIXTURES

    def setUp(self):
        self.followup_org = Organization.objects.filter(
            needs_applicant_followups=True).first()
        self.non_followup_org = Organization.objects.filter(
            needs_applicant_followups=False, is_receiving_agency=True).first()

    def test_filters_out_new_submissions(self):
        # NOTE: this seems to raise a warning:
        # RuntimeWarning: DateTimeField FormSubmission.date_received
        # received a naive datetime (2016-11-07 00:00:00) while time zone
        # support is active.
        # but the datetime sent is definitely not naive, and the resulting
        # value of date_received is correct.
        # I don't know what causes the warning
        # given new submissions and older submissions
        old_sub = factories.FormSubmissionWithOrgsFactory.create(
            date_received=get_old_date(), organizations=[self.followup_org])
        new_sub = factories.FormSubmissionWithOrgsFactory.create(
            date_received=get_newer_date(), organizations=[self.followup_org])
        # we should only get submissions that are newer
        results = FollowupsService.get_submissions_due_for_follow_ups()
        results_set = set(results)
        self.assertIn(old_sub, results_set)
        self.assertNotIn(new_sub, results_set)

    def test_filters_out_subs_with_previous_followups(self):
        # given old submissions, some with old followups
        no_followup = factories.FormSubmissionWithOrgsFactory.create(
            date_received=get_old_date(), organizations=[self.followup_org])
        applicant = factories.ApplicantFactory()
        sub_w_followup = factories.FormSubmissionWithOrgsFactory.create(
            date_received=get_old_date(),
            applicant=applicant, organizations=[self.followup_org],
            has_been_sent_followup=True)
        # if we grab subs that need followups
        results = FollowupsService.get_submissions_due_for_follow_ups()
        results_set = set(results)
        # we should only have ones that have not received followups
        self.assertIn(no_followup, results_set)
        self.assertNotIn(sub_w_followup, results_set)

    def test_filters_out_subs_with_previous_followup_flag(self):
        # given old submissions, some with old followups
        no_followup = factories.FormSubmissionWithOrgsFactory.create(
            date_received=get_old_date(), organizations=[self.followup_org])
        sub_w_followup = factories.FormSubmissionWithOrgsFactory.create(
            date_received=get_old_date(), organizations=[self.followup_org],
            has_been_sent_followup=True)
        # if we grab subs that need followups
        results = FollowupsService.get_submissions_due_for_follow_ups()
        results_set = set(results)
        # we should only have ones that have not been flagged
        self.assertIn(no_followup, results_set)
        self.assertNotIn(sub_w_followup, results_set)

    def test_can_start_at_particular_id_to_create_time_interval(self):
        # assume we have 4 old subs, 1 new sub
        old_subs = sorted([
            factories.FormSubmissionWithOrgsFactory.create(
                date_received=get_old_date(),
                organizations=[self.followup_org])
            for i in range(4)
        ], key=lambda s: s.date_received)
        new_sub = factories.FormSubmissionWithOrgsFactory.create(
            date_received=get_newer_date(), organizations=[self.followup_org])
        # but we only want ones after the second oldest sub
        second_oldest_id = old_subs[1].id
        # and within the old subs, we still don't want ones that already
        #   received followups
        applicant = factories.ApplicantFactory()
        followed_up_sub = old_subs[2]
        followed_up_sub.applicant = applicant
        followed_up_sub.has_been_sent_followup = True
        followed_up_sub.save()
        # when we get submissions due for follow ups,
        results = list(FollowupsService.get_submissions_due_for_follow_ups(
            after_id=second_oldest_id))
        # we should only receive two:
        self.assertEqual(len(results), 2)
        #   the second oldest
        self.assertIn(old_subs[1], results)
        #   and not-as-old one that did not have a follow up
        self.assertIn(old_subs[3], results)
        # we should not receive
        #   the oldest sub
        self.assertNotIn(old_subs[0], results)
        #   the one with the follow up
        self.assertNotIn(followed_up_sub, results)
        #   or the new sub
        self.assertNotIn(new_sub, results)

    def test_excludes_subs_w_updates_from_all_orgs(self):
        orgs = [self.followup_org, self.non_followup_org]
        sub_to_exclude = factories.FormSubmissionWithOrgsFactory.create(
            organizations=list(orgs),
            date_received=get_old_date())
        sub_to_include = factories.FormSubmissionWithOrgsFactory.create(
            organizations=list(orgs),
            date_received=get_old_date())
        for app in sub_to_exclude.applications.all():
            factories.StatusUpdateWithNotificationFactory.create(
                application=app)
        results = list(FollowupsService.get_submissions_due_for_follow_ups())
        self.assertNotIn(sub_to_exclude, results)
        self.assertIn(sub_to_include, results)

    def test_excludes_subs_w_all_non_followup_orgs(self):
        sub_to_include = factories.FormSubmissionWithOrgsFactory.create(
            date_received=get_old_date(), organizations=[self.followup_org])
        sub_to_exclude = factories.FormSubmissionWithOrgsFactory.create(
            date_received=get_old_date(),
            organizations=[self.non_followup_org])
        results = list(FollowupsService.get_submissions_due_for_follow_ups())
        self.assertNotIn(sub_to_exclude, results)
        self.assertIn(sub_to_include, results)

    def test_includes_subs_w_one_followup_org(self):
        sub = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[self.followup_org, self.non_followup_org],
            date_received=get_old_date())
        results = list(FollowupsService.get_submissions_due_for_follow_ups())
        self.assertIn(sub, results)


class TestSendFollowupNotifications(ExternalNotificationsPatchTestCase):
    fixtures = ESSENTIAL_DATA_FIXTURES + MOCK_USER_ACCOUNT_FIXTURES

    def setUp(self):
        super().setUp()
        self.followup_org = Organization.objects.filter(
            needs_applicant_followups=True).first()
        self.non_followup_org = Organization.objects.filter(
            needs_applicant_followups=False, is_receiving_agency=True).first()

    def full_answers(self):
        org = Organization.objects.get(slug='a_pubdef')
        return get_answers_for_orgs(
            [org],
            contact_preferences=[
                'prefers_email',
                'prefers_sms',
                'prefers_voicemail',
                'prefers_snailmail'],
            email='test@testing.com',
            phone_number='4152124848'
        )

    def cant_contact_answers(self):
        org = Organization.objects.get(slug='a_pubdef')
        return get_answers_for_orgs(
            [org],
            contact_preferences=[
                'prefers_voicemail',
                'prefers_snailmail'],
            email='test@testing.com',
            phone_number='4152124848'
        )

    def test_case_when_all_have_usable_contact_info(self):
        orgs = [
            Organization.objects.get(slug='a_pubdef')]
        subs = []
        for i in range(4):
            subs.append(factories.FormSubmissionWithOrgsFactory.create(
                organizations=orgs,
                answers=self.full_answers(),
            ))
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            FollowupsService.send_followup_notifications(subs)
        self.assertEqual(
            FollowupsService.get_submissions_due_for_follow_ups().count(), 0)
        self.assertEqual(
            len(self.notifications.email_followup.send.mock_calls), 4)
        self.assertEqual(
            len(self.notifications.sms_followup.send.mock_calls), 0)
        assertInLogsCount(logs, {'event_name=app_followup_sent': 4})
        for sub in subs:
            assertInLogsCount(logs, {'distinct_id=' + sub.get_uuid(): 1})
            self.assertEqual(sub.has_been_sent_followup, True)

    def test_if_some_have_usable_contact_info(self):
        orgs = [
            Organization.objects.get(slug='a_pubdef')]
        contacted_subs = []
        for i in range(2):
            contacted_subs.append(
                factories.FormSubmissionWithOrgsFactory.create(
                    organizations=orgs,
                    answers=self.full_answers()))
        not_contacted_subs = []
        for i in range(2):
            not_contacted_subs.append(
                factories.FormSubmissionWithOrgsFactory.create(
                    organizations=orgs,
                    answers=self.cant_contact_answers()))
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            FollowupsService.send_followup_notifications(
                contacted_subs + not_contacted_subs)
        self.assertEqual(
            FollowupsService.get_submissions_due_for_follow_ups().count(), 0)
        self.assertEqual(
            len(self.notifications.email_followup.send.mock_calls), 2)
        self.assertEqual(
            len(self.notifications.sms_followup.send.mock_calls), 0)
        assertInLogsCount(logs, {'event_name=app_followup_sent': 2})
        for sub in contacted_subs:
            assertInLogsCount(logs, {'distinct_id=' + sub.get_uuid(): 1})
            self.assertEqual(sub.has_been_sent_followup, True)
        for sub in not_contacted_subs:
            assertInLogsCount(logs, {'distinct_id=' + sub.get_uuid(): 0})
            self.assertEqual(sub.has_been_sent_followup, False)

    def test_that_followup_messages_arent_sent_for_apps_w_updates(self):
        org_a, org_b = Organization.objects.filter(
            is_receiving_agency=True)[:2]
        sub = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[org_a, org_b])
        sub.answers.update(
            phone_number='8314207603', contact_preferences=['prefers_sms'])
        sub.save()
        updated_app = sub.applications.filter(organization_id=org_a.id).first()
        author = org_a.profiles.first().user
        factories.StatusUpdateWithNotificationFactory.create(
            application=updated_app, author=author)
        FollowupsService.send_followup_notifications([sub])
        mock_args, mock_kwargs = self.notifications.sms_followup.send.call_args
        self.assertNotIn(
            org_a.short_followup_message, mock_kwargs['followup_messages'])

    def test_that_followup_messages_only_include_followup_orgs(self):
        sub = factories.FormSubmissionWithOrgsFactory.create(
            organizations=[self.non_followup_org, self.followup_org])
        sub.answers.update(
            phone_number='8314207603', contact_preferences=['prefers_sms'])
        sub.save()
        FollowupsService.send_followup_notifications([sub])
        mock_args, mock_kwargs = self.notifications.sms_followup.send.call_args
        self.assertNotIn(
            self.non_followup_org.short_followup_message,
            mock_kwargs['followup_messages'])
        self.assertIn(
            self.followup_org.short_followup_message,
            mock_kwargs['followup_messages'])
