from django.db.models import Count
from intake import models, exceptions
import intake.services.applications_service as AppsService
from user_accounts.models import Organization


# def get_or_create_prebuilt_pdf():
#     unread_applications = AppsService.get_unread_applications_for_org(
#         sf_pubdef)
#     # do these apps have an up-to-date-prefilled-pdf?
#     prebuilt = models.PrebuiltMultiAppPDF.objects.filter(
#         organization=sf_pubdef)
#     unread_app_ids = unread_applications.values_list('id', flat=True)
#     prebuilt_app_ids = prebuilt.applications.values_list('id', flat=True)
#     has_correct_prebuilt_apps = set(unread_app_ids) == set(prebuilt_app_ids)
#     if not has_correct_prebuilt_apps:
#         prebuild_unread_apps_pdf(unread_app_ids, prebuilt)

def prebuild_newapps_pdf_for_san_francisco():
    # get unread applications
    sf_pubdef = Organization.objects.get(slug='sf_pubdef')
    unread_apps = AppsService.get_unread_applications_for_org(sf_pubdef)
    unread_app_ids = [app.id for app in unread_apps]
    unread_apps_without_pdfs = models.Application.objects.annotate(
        filled_pdf_count=Count('form_submission')
    ).filter(id__in=unread_app_ids, filled_pdf_count=0)
    filled_pdfs = models.FilledPDF.objects.filter(
        submission__applications__id__in=[app.id for app in unread_apps])



    # for any unreads that do not have a pdf, make one (and alert)
    # concatenate all the pdfs together


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
    return models.PrebuiltMultiAppPDF.objects.filter(
            applications__id=application_id).exists()


def rebuild_newapps_pdf_for_new_application(application_id):
    if not newapps_pdf_includes_app(application_id):
        prebuild_newapps_pdf_for_san_francisco()


def rebuild_newapps_pdf_for_removed_application(application_id):
    if newapps_pdf_includes_app(application_id):
        prebuild_newapps_pdf_for_san_francisco()
