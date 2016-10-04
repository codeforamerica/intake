from intake import (
    notifications,
    models as intake_models
)
from user_accounts.models import Organization


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

    def get_submission_ids(self):
        return [submission.id for submission in self.submissions]

    def create_app_bundle(self):
        return intake_models.ApplicationBundle.create_with_submissions(
            submissions=self.submissions,
            organization=self.organization,
        )

    def make_referrals(self):
        """Send notifications to self.organization users
        with the bundle of submissions
        Log the referral, and send a report to slack
        """
        count = len(self.submissions)
        ids = self.get_submission_ids()
        app_bundle = self.create_app_bundle()
        bundle_url = app_bundle.get_external_url()
        notifications.front_email_daily_app_bundle.send(
            to=self.notification_emails,
            count=count,
            bundle_url=bundle_url
        )
        intake_models.ApplicationLogEntry.log_referred(
            ids, user=None, organization=self.organization)
        notifications.slack_app_bundle_sent.send(
            submissions=self.submissions,
            emails=self.notification_emails,
            bundle_url=bundle_url
            )


class SubmissionBundler:
    """Responsible for making a query to
    get the relevant submissions, bundling up submissions,
    and telling the bundles to send notifications
    """

    def __init__(self):
        self.organization_bundle_map = {}

    def get_org_referral(self, organization):
        """Get or create an OrganizationBundle, based on org id
        """
        bundle = self.organization_bundle_map.get(
            organization.id, OrganizationBundle(organization))
        self.organization_bundle_map[organization.id] = bundle
        return bundle

    def map_submissions_to_orgs(self):
        """Loop through receiving orgs and get unopened apps for each
        """
        for receiving_org in Organization.objects.filter(
                is_receiving_agency=True):
            bundle = self.get_org_referral(receiving_org)
            bundle.submissions = receiving_org.get_unopened_apps()

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
