
from intake import (
    notifications,
    models as intake_models
)
from user_accounts import models as auth_models


class OrganizationBundle:
    """A simple class to link an organization,
    submissions destined for that organization,
    and emails of users to notify at the org.
    This object is responsible for sending notifications
    and logging the referral
    """

    def __init__(self, organization):
        self.organization = organization
        self.submissions = []
        self.notification_emails = organization.get_referral_emails()

    def add_submission(self, submission):
        self.submissions.append(submission)

    def get_submission_ids(self):
        return [submission.id for submission in self.submissions]

    def make_referrals(self):
        """Send notifications to self.organization users
        with the bundle of submissions
        Log the referral, and send a report to slack
        """
        count = len(self.submissions)
        ids = self.get_submission_ids()
        notifications.front_email_daily_app_bundle.send(
            to=self.notification_emails,
            count=count,
            submission_ids=ids
        )
        intake_models.ApplicationLogEntry.log_referred(
            ids, user=None, organization=self.organization)
        notifications.slack_app_bundle_sent.send(
            submissions=self.submissions,
            emails=self.notification_emails)


class SubmissionBundler:
    """Responsible for making a query to
    get the relevant submissions, bundling up submissions,
    and telling the bundles to send notifications
    """

    def __init__(self):
        self.queryset = intake_models.FormSubmission.get_unopened_apps().prefetch_related(
            'counties',
            'counties__organizations',
            'counties__organizations__profiles',
            'counties__organizations__profiles__user').all()
        self.organization_bundle_map = {}

    def get_org_referral(self, organization):
        """Get or create an OrganizationBundle, based on org id
        """
        bundle = self.organization_bundle_map.get(
            organization.id, OrganizationBundle(organization))
        self.organization_bundle_map[organization.id] = bundle
        return bundle

    def map_submissions_to_orgs(self):
        """Run through the query set and add each submissions to the
        appropriate OrganizationBundle
        """
        for submission in self.queryset:
            for county in submission.counties.all():
                receiving_org = county.get_receiving_agency()
                bundle = self.get_org_referral(receiving_org)
                bundle.add_submission(submission)

    def make_bundled_referrals(self):
        """Make bundles and tell them to send out referrals
        """
        self.map_submissions_to_orgs()
        for bundle in self.organization_bundle_map.values():
            bundle.make_referrals()


def bundle_and_notify():
    """Bundles submissions by organization and sends notifications
    to the designated receiving emails for that organization
    """
    bundler = SubmissionBundler()
    bundler.make_bundled_referrals()
    return bundler
