from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from intake import (
    notifications,
    models as intake_models
)


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

    def create_app_bundle(self):
        filled_pdfs = intake_models.FilledPDF.objects.filter(
            submission__in=self.submissions)
        bundle = intake_models.ApplicationBundle(
            organization=self.organization,
        )
        if filled_pdfs:
            # TODO: test that the pdf is made properly
            pdf_objects = [filled.pdf for filled in filled_pdfs]
            bundled_pdf_bytes = intake_models.get_parser().join_pdfs(
                pdf_objects)
            now_str = timezone.now().strftime('%Y-%m-%d_%H:%M')
            filename = "submission_bundle_{0:0>4}-{1}.pdf".format(
                self.organization.pk, now_str)
            pdf_file = SimpleUploadedFile(filename, bundled_pdf_bytes,
                                          content_type='application/pdf')
            bundle.bundled_pdf = pdf_file
        bundle.save()
        bundle.submissions.add(*self.submissions)
        return bundle

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
        self.queryset = intake_models.FormSubmission.get_unopened_apps()\
                            .prefetch_related(
                                'organizations',
                                'organizations__profiles',
                                'organizations__profiles__user'
                            ).all()
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
            for receiving_org in submission.organizations.all():
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
