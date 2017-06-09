from django.db.models import Count
from django.utils import timezone as timezone_utils
from django.core.files.uploadedfile import SimpleUploadedFile
from intake import models, exceptions, constants
import intake.services.applications_service as AppsService
from user_accounts.models import Organization


def set_single_newapps_pdf_to_bytes(bytes_):
    prebuilts = models.NewAppsPDF.objects.filter(
        organization__slug='sf_pubdef')
    if prebuilts.count() > 1:
        raise exceptions.MultiplePrebuiltPDFsError(
            "{} prebuilt pdfs found. There should only be 1.")
    prebuilt = prebuilts.first()
    now_str = timezone_utils.now().astimezone(
        constants.PACIFIC_TIME).strftime('%Y-%m-%d_%H:%M')
    filename = 'sf_pubdef_new_apps_{}.pdf'.format(now_str)
    prebuilt.pdf = SimpleUploadedFile(
        filename, bytes_, content_type='application/pdf')
    prebuilt.save()
    return prebuilt


def prebuild_newapps_pdf_for_san_francisco():
    # get unread applications
    # for any unreads that do not have a pdf, make one (and alert)
    # concatenate all the pdfs together
    sf_pubdef = Organization.objects.get(slug='sf_pubdef')
    unread_apps = AppsService.get_unread_applications_for_org(sf_pubdef)
    unread_app_ids = [app.id for app in unread_apps]
    unread_apps_without_pdfs = models.Application.objects.annotate(
        filled_pdf_count=Count('form_submission')
    ).filter(id__in=unread_app_ids, filled_pdf_count=0)
    for app in unread_apps_without_pdfs:
        fill_pdf_for_application(app.id)
    filled_pdfs = models.FilledPDF.objects.filter(
        submission__applications__id__in=unread_app_ids)
    return set_single_newapps_pdf_to_bytes(
        models.get_parser().join_pdfs(
            filled.pdf for filled in filled_pdfs))


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


def newapps_pdf_includes_app(application_id):
    return models.NewAppsPDF.objects.filter(
            applications__id=application_id).exists()


def rebuild_newapps_pdf_for_new_application(application_id):
    if not newapps_pdf_includes_app(application_id):
        prebuild_newapps_pdf_for_san_francisco()


def rebuild_newapps_pdf_for_removed_application(application_id):
    if newapps_pdf_includes_app(application_id):
        prebuild_newapps_pdf_for_san_francisco()
