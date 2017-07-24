from django.db.models import Count
from project import alerts
from intake import models, exceptions, utils
import intake.services.applications_service as AppsService
from user_accounts.models import Organization
import intake.services.display_form_service as DisplayFormService
from printing.pdf_form_display import PDFFormDisplay


def fill_pdf_for_application(application_id):
    """Returns a Filled PDF for the given application_id
    Raises an error if no fillable pdf exists or or if it has no file loaded.
    """
    app = models.Application.objects.get(id=application_id)
    fillable_pdf = models.FillablePDF.objects.filter(
        organization_id=app.organization_id).first()
    if not fillable_pdf or not fillable_pdf.pdf:
        raise exceptions.MissingFillablePDFError(
            "{org_name} lacks a pdf to fill for {app}".format(
                org_name=app.organization.name, app=app))
    return models.FilledPDF.create_with_pdf_bytes(
        pdf_bytes=fillable_pdf.fill(app.form_submission),
        original_pdf=fillable_pdf,
        submission=app.form_submission)


def get_prebuilt_pdf_bundle_for_app_id_set(app_ids):
    # match the number of IDs
    # order_by('created') is used to create deterministic results
    # for testing purposes
    matching_bundles = models.PrebuiltPDFBundle.objects.annotate(
        app_count=Count('applications')
    ).filter(app_count=len(app_ids)).order_by('created')
    # ensure it includes each ID
    for app_id in app_ids:
        matching_bundles = matching_bundles.filter(applications__id=app_id)
    return matching_bundles.first()


def set_bytes_to_filled_pdfs(instance, filled_pdfs):
    if len(filled_pdfs) == 0:
        instance.pdf = None
    elif len(filled_pdfs) == 1:
        instance.set_bytes(filled_pdfs[0].pdf.read())
    else:
        instance.set_bytes(
            models.get_parser().join_pdfs(
                filled.pdf for filled in filled_pdfs))
    instance.save()


def fill_any_unfilled_pdfs_for_app_ids(app_ids):
    apps_without_pdfs = models.Application.objects.annotate(
        filled_pdf_count=Count('form_submission__filled_pdfs')
    ).filter(id__in=app_ids, filled_pdf_count=0)
    # build individual filled pdfs if necessary
    for app in apps_without_pdfs:
        fill_pdf_for_application(app.id)
    if apps_without_pdfs:
        message = '{} apps did not have PDFs:\n'.format(len(apps_without_pdfs))
        message += '\n'.join([str(app) for app in apps_without_pdfs])
        alerts.send_email_to_admins(
            subject='No FilledPDFs for Applications', message=message)


def get_or_create_prebuilt_pdf_for_app_ids(app_ids):
    prebuilt = get_prebuilt_pdf_bundle_for_app_id_set(app_ids)
    if not prebuilt:
        subject = 'Missing Prebuilt PDF Bundle'
        message = \
            'Querying with ids \n{}\ndid not return a prebuilt pdf'.format(
                app_ids)
        alerts.send_email_to_admins(subject=subject, message=message)
        prebuilt = update_pdf_bundle_for_san_francisco()
    return prebuilt


def create_new_pdf_bundle_for_apps(org, apps):
    app_ids = [app.id for app in apps]
    pdf_bundle = models.PrebuiltPDFBundle(organization_id=org.id)
    pdf_bundle.save()
    pdf_bundle.applications.add(*apps)
    fill_any_unfilled_pdfs_for_app_ids(app_ids)
    filled_pdfs = models.FilledPDF.objects.filter(
        submission__applications__id__in=app_ids)
    set_bytes_to_filled_pdfs(pdf_bundle, filled_pdfs)
    return pdf_bundle


def update_pdf_bundle_for_san_francisco():
    """Gets or creates a PrebuiltPDFBundle for San Francisco
        links it to all the unread applications
        and rebuilds the PDF
    """
    sf_pubdef = Organization.objects.get(slug='sf_pubdef')
    unread_apps = AppsService.get_unread_applications_for_org(sf_pubdef)
    if unread_apps.count() > 0:
        app_ids = [app.id for app in unread_apps]
        pdf_bundle = get_prebuilt_pdf_bundle_for_app_id_set(app_ids)
        if not pdf_bundle:
            pdf_bundle = create_new_pdf_bundle_for_apps(sf_pubdef, unread_apps)
        return pdf_bundle


def rebuild_pdf_bundle_for_removed_application(application_id):
    app_is_for_org_with_fillable = models.FillablePDF.objects.filter(
        organization__applications__id=application_id).exists()
    if app_is_for_org_with_fillable:
        update_pdf_bundle_for_san_francisco()


def get_applicant_name(form):
    return '{}, {}'.format(
        form.last_name.get_display_value(),
        ' '.join([
            n for n in [
                form.first_name.get_display_value(),
                form.middle_name.get_display_value()
            ] if n
        ])
    )


def get_printout_for_submission(user, submission):
    # get the correct form
    form, letter = DisplayFormService.get_display_form_for_user_and_submission(
        user, submission)
    # use the form to serialize the submission
    pdf_display = PDFFormDisplay(form, letter)
    canvas, pdf = pdf_display.render(
        title=get_applicant_name(form) + " - Case Details")
    filename = '{}-{}-{}-CaseDetails.pdf'.format(
        form.last_name.get_display_value(),
        form.first_name.get_display_value(),
        submission.id)
    pdf.seek(0)
    return filename, pdf.read()


def get_printout_for_application(application):
    form, letter = DisplayFormService.get_display_form_for_application(
        application)
    pdf_display = PDFFormDisplay(form, letter)
    canvas, pdf = pdf_display.render(
        title=get_applicant_name(form) + "- Case Details")
    filename = '{}-{}-{}-CaseDetails.pdf'.format(
        form.last_name.get_display_value(),
        form.first_name.get_display_value(),
        application.form_submission_id)
    pdf.seek(0)
    return filename, pdf.read()


def concatenated_printout(form_letter_tuples):
    canvas = None
    pdf_file = None
    count = len(form_letter_tuples)
    for i, form_letter_tuple in enumerate(form_letter_tuples):
        if i == 0:
            pdf_display = PDFFormDisplay(*form_letter_tuple)
            canvas, pdf_file = pdf_display.render(save=False)
        else:
            pdf_display = PDFFormDisplay(*form_letter_tuple, canvas=canvas)
            if i == (count - 1):
                canvas, pdf = pdf_display.render(
                    save=True,
                    title="{} Applications from Code for America".format(
                        count))
            else:
                canvas, pdf = pdf_display.render(save=False)
    today = utils.get_todays_date()
    filename = '{}-{}-Applications-CodeForAmerica.pdf'.format(
        today.strftime('%Y-%m-%d'), count)
    pdf_file.seek(0)
    return filename, pdf_file.read()


def get_concatenated_printout_for_bundle(user, bundle):
    submissions = list(bundle.submissions.all())
    count = len(submissions)
    if count == 1:
        return get_printout_for_submission(user, submissions[0])
    else:
        return concatenated_printout([
            DisplayFormService.get_display_form_for_user_and_submission(
                user, submission)
            for submission in submissions])


def get_concatenated_printout_for_applications(applications):
    count = len(applications)
    if count == 1:
        return get_printout_for_application(applications[0])
    else:
        return concatenated_printout([
            DisplayFormService.get_display_form_for_application(app)
            for app in applications])
