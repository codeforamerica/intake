from formation.forms import (
    display_form_selector, DeclarationLetterDisplay)


def instantiate_display_form_with_submission(form_class, submission):
    """Feed a submission and its associated data into a display form class
    """
    # one query to get all related objects
    orgs = list(submission.organizations.select_related('county'))
    county_slugs = [org.county.slug for org in orgs]
    init_data = dict(
        date_received=submission.get_local_date_received(),
        counties=county_slugs,
        organizations=[org.name for org in orgs])
    init_data.update(submission.answers)
    display_form = form_class(init_data, validate=True)
    display_form.display_only = True
    display_form.display_template_name = "formation/intake_display.jinja"
    display_form.submission = submission
    show_declaration = any(map(lambda o: o.requires_declaration_letter, orgs))
    if show_declaration:
        declaration_letter_form = DeclarationLetterDisplay(
            init_data, validate=True)
        return display_form, declaration_letter_form
    return display_form, None


def get_display_form_for_user_and_submission(user, submission):
    """
    based on user information, get the correct Form class and return it
    instantiated with the data from submission
    """
    if not user.is_staff:
        # get the county for the shared org between user and submission
        DisplayFormClass = display_form_selector.get_combined_form_class(
            counties=submission.organizations.filter(
                profiles__user__id=user.id
            ).values_list('county__slug', flat=True))
    else:
        DisplayFormClass = display_form_selector.get_combined_form_class(
            counties=submission.organizations.values_list(
                'county__slug', flat=True))
    return instantiate_display_form_with_submission(
        DisplayFormClass, submission)


def get_display_form_for_application(application):
    """Returns a display form based on the organization an application is
    destined for
    """
    DisplayFormClass = display_form_selector.get_combined_form_class(
        counties=[application.organization.county.slug])
    return instantiate_display_form_with_submission(
        DisplayFormClass, application.form_submission)
