import logging
import intake
from intake.models import ApplicationBundle, get_parser
import intake.services.submissions as SubmissionsService


logger = logging.getLogger(__name__)


def create_bundle_from_submissions(submissions, skip_pdf=False, **kwargs):
    bundle = ApplicationBundle(**kwargs)
    bundle.save()
    if submissions:
        bundle.submissions.add(*submissions)
    if not skip_pdf and not bundle.bundled_pdf:
        build_bundled_pdf_if_necessary(bundle)
    return bundle


def get_or_create_for_submissions_and_user(submissions, user):
        query = ApplicationBundle.objects.all()
        for sub in submissions:
            query = query.filter(submissions=sub)
        if not user.is_staff:
            query = query.filter(organization=user.profile.organization)
        query = query.first()
        if not query:
            query = create_bundle_from_submissions(
                submissions,
                organization=user.profile.organization)
        return query


def build_bundled_pdf_if_necessary(bundle):
    """Populates `bundled_pdf` attribute if needed

    First checks whether or not there should be a pdf. If so,
    - tries to grab filled pdfs for the bundles submissions
    - if it needs a pdf but there weren't any pdfs, it logs an error and
      creates the necessary filled pdfs.
    - makes a filename based on the organization and current time.
    - adds the file data and saves itself.
    """
    needs_pdf = bundle.should_have_a_pdf()
    if not needs_pdf:
        return
    submissions = bundle.submissions.all()
    filled_pdfs = bundle.get_individual_filled_pdfs()
    missing_filled_pdfs = (
        not filled_pdfs or (len(submissions) > len(filled_pdfs)))
    if needs_pdf and missing_filled_pdfs:
        msg = str(
            "Submissions for ApplicationBundle(pk={}) lack pdfs"
            ).format(bundle.pk)
        logger.error(msg)
        intake.notifications.slack_simple.send(msg)
        for submission in submissions:
            SubmissionsService.fill_pdfs_for_submission(submission)
        filled_pdfs = bundle.get_individual_filled_pdfs()
    if len(filled_pdfs) == 1:
        bundle.set_bundled_pdf_to_bytes(filled_pdfs[0].pdf.read())
    else:
        bundle.set_bundled_pdf_to_bytes(
            get_parser().join_pdfs(
                filled.pdf for filled in filled_pdfs))
    bundle.save()
