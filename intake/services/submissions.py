from intake import models as intake_models


class MissingAnswersError(Exception):
    pass


def create_submission(form, organizations, applicant_id):
        """Save the submission data
        """
        submission = intake_models.FormSubmission(
            answers=form.cleaned_data,
            applicant_id=applicant_id)
        submission.save()
        submission.organizations.add(*organizations)
        intake_models.ApplicationEvent.log_app_submitted(applicant_id)
        return submission


def fill_pdfs_for_submission(submission):
    """Checks for and creates any needed `FilledPDF` objects
    """
    fillables = intake_models.FillablePDF.objects.filter(
        organization__submissions=submission)
    for fillable in fillables:
        fillable.fill_for_submission(submission)


def get_permitted_submissions(user, ids=None, related_objects=False):
    query = intake_models.FormSubmission.objects
    if related_objects:
        query = query.prefetch_related(
            'logs__user__profile__organization')
    if ids:
        query = query.filter(pk__in=ids)
    if user.is_staff:
        return query.all()
    org = user.profile.organization
    return query.filter(organizations=org)


""" These methods are used for test setup only """


def create_for_organizations(organizations, **kwargs):
    submission = intake_models.FormSubmission(**kwargs)
    submission.save()
    submission.organizations.add(*organizations)
    return submission


def create_for_counties(counties, **kwargs):
    if 'answers' not in kwargs:
        msg = ("'answers' are needed to infer organizations "
               "for a form submission")
        raise MissingAnswersError(msg)
    organizations = [
        county.get_receiving_agency(kwargs['answers'])
        for county in counties
    ]
    return create_for_organizations(
        organizations=organizations, **kwargs)
