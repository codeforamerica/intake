from unittest.mock import patch
from django.test import TestCase

import intake.services.followups as FollowupsService
from intake.tests import mock
from intake.constants import PACIFIC_TIME, Organizations
from intake import models
from user_accounts.models import Organization

"""
Each function in intake.services.followups corresponds to a TestCase in this
file.
"""


def get_old_date():
    return PACIFIC_TIME.localize(mock.fake.date_time_between('-8w', '-5w'))


def get_newer_date():
    return PACIFIC_TIME.localize(mock.fake.date_time_between('-3w', 'now'))


class TestGetSubmissionsDueForFollowups(TestCase):

    def test_filters_out_new_submissions(self):
        # NOTE: this seems to raise a warning:
            # RuntimeWarning: DateTimeField FormSubmission.date_received
            # received a naive datetime (2016-11-07 00:00:00) while time zone
            # support is active.
        # but the datetime sent is definitely not naive, and the resulting
        # value of date_received is correct.
        # I don't know what causes the warning
        # given new submissions and older submissions
        old_sub = mock.FormSubmissionFactory.create(
            date_received=get_old_date())
        new_sub = mock.FormSubmissionFactory.create(
            date_received=get_newer_date())
        # we should only get submissions that are newer
        results = FollowupsService.get_submissions_due_for_follow_ups()
        results_set = set(results)
        self.assertIn(old_sub, results_set)
        self.assertNotIn(new_sub, results_set)

    def test_filters_out_subs_with_previous_followups(self):
        # given old submissions, some with old followups
        no_followup = mock.FormSubmissionFactory.create(
            date_received=get_old_date())
        applicant = models.Applicant()
        applicant.save()
        sub_w_followup = mock.FormSubmissionFactory.create(
            date_received=get_old_date(),
            applicant=applicant)
        models.ApplicationEvent.log_followup_sent(
            applicant.id,
            contact_info=sub_w_followup.answers['email'],
            message="hey how are things going?")
        # if we grab subs that need followups
        results = FollowupsService.get_submissions_due_for_follow_ups()
        results_set = set(results)
        # we should only have ones that have not received followups
        self.assertIn(no_followup, results_set)
        self.assertNotIn(sub_w_followup, results_set)

    def test_can_start_at_particular_id_to_create_time_interval(self):
        # assume we have 4 old subs, 1 new sub
        old_subs = sorted([
            mock.FormSubmissionFactory.create(date_received=get_old_date())
            for i in range(4)
            ], key=lambda s: s.date_received)
        new_sub = mock.FormSubmissionFactory.create(
            date_received=get_newer_date())
        # but we only want ones after the second oldest sub
        second_oldest_id = old_subs[1].id
        # and within the old subs, we still don't want ones that already
        #   received followups
        applicant = models.Applicant()
        applicant.save()
        followed_up_sub = old_subs[2]
        followed_up_sub.applicant = applicant
        followed_up_sub.save()
        models.ApplicationEvent.log_followup_sent(
            applicant.id,
            contact_info=followed_up_sub.answers['email'],
            message="hey how are things going?")
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


class TestSendFollowupNotification(TestCase):

    fixtures = ['counties', 'organizations']

    @patch('intake.notifications.check_that_remote_connections_are_okay')
    @patch('intake.notifications.json')
    def test_expected_result(self, mock_json, ext_conn_check):
        ext_conn_check.return_value = False
        mock_json.dumps.return_value = "a mock_json"
        orgs = list(Organization.objects.filter(
            slug__in=[
                Organizations.ALAMEDA_PUBDEF,
                Organizations.SF_PUBDEF,
                Organizations.MONTEREY_PUBDEF,
            ]))
        answers = mock.fake.all_county_answers(
            first_name="Hubert",
            contact_preferences=[
                'prefers_email',
                'prefers_sms',
                'prefers_voicemail',
                'prefers_snailmail'
            ],
            email='test@gmail.com',
            )
        mock.FormSubmissionFactory.create(
            date_received=get_old_date(),
            anonymous_name="Cerulean Beetle",
            organizations=orgs,
            answers=answers)
        results = FollowupsService.get_contactable_followups()
        FollowupsService.send_followup_notification(results[0])

        dict_for_front = mock_json.dumps.mock_calls[0][1][0]
        message_text = dict_for_front['text']
        self.assertEqual(dict_for_front['to'], answers['email'])

        self.assertIn("Hello again Hubert,", message_text)
        self.assertIn(
            str("You applied online about one month ago for help in San "
                "Francisco, Alameda, and Monterey counties"),
            message_text)
        for org in orgs:
            self.assertIn(org.long_followup_message, message_text)
        # we should have sent two external requests
        self.assertEqual(len(ext_conn_check.mock_calls), 2)

    @patch('intake.notifications.check_that_remote_connections_are_okay')
    @patch('intake.notifications.json')
    def test_with_sms(self, mock_json, ext_conn_check):
        ext_conn_check.return_value = False
        mock_json.dumps.return_value = "a mock_json"
        orgs = list(Organization.objects.filter(
            slug__in=[
                Organizations.ALAMEDA_PUBDEF,
                Organizations.SF_PUBDEF,
                Organizations.MONTEREY_PUBDEF,
            ]))
        answers = mock.fake.all_county_answers(
            first_name="Hubert",
            contact_preferences=[
                'prefers_sms',
                'prefers_voicemail',
                'prefers_snailmail'
            ],
            phone_number='555-555-5555',
            )
        mock.FormSubmissionFactory.create(
            date_received=get_old_date(),
            anonymous_name="Cerulean Beetle",
            organizations=orgs,
            answers=answers)
        results = FollowupsService.get_contactable_followups()
        FollowupsService.send_followup_notification(results[0])
        dict_for_front = mock_json.dumps.mock_calls[0][1][0]
        message_text = dict_for_front['text']
        self.assertTrue(len(message_text) < 500)

    @patch('intake.notifications.check_that_remote_connections_are_okay')
    @patch('intake.notifications.json')
    def test_with_no_contact_info(self, mock_json, ext_conn_check):
        ext_conn_check.return_value = False
        mock_json.dumps.return_value = "a mock_json"
        orgs = list(Organization.objects.filter(
            slug__in=[
                Organizations.ALAMEDA_PUBDEF,
                Organizations.SF_PUBDEF,
                Organizations.MONTEREY_PUBDEF,
            ]))
        answers = mock.fake.all_county_answers(
            first_name="Hubert",
            contact_preferences=[
                'prefers_voicemail',
                'prefers_snailmail'
            ]
            )
        mock.FormSubmissionFactory.create(
            date_received=get_old_date(),
            anonymous_name="Cerulean Beetle",
            organizations=orgs,
            answers=answers)
        results = FollowupsService.get_serialized_follow_up_subs()
        FollowupsService.send_followup_notification(results[0])
        dict_for_slack = mock_json.dumps.mock_calls[0][1][0]
        self.assertIn(
            "Did not send a followup to Cerulean Beetle",
            dict_for_slack['text'])
