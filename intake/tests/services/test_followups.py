
from django.test import TestCase

import intake.services.followups as FollowupsService
from intake.tests import mock
from intake.constants import PACIFIC_TIME
from intake import models

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


class TestGetFollowupsCount(TestCase):

    def test_count_is_correct(self):
        for i in range(5):
            mock.FormSubmissionFactory.create(date_received=get_old_date())
        result = FollowupsService.get_followups_count()
        self.assertEqual(result, 5)
