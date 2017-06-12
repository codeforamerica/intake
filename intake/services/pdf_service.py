from django.db.models import Count
from intake import models, exceptions
import intake.services.applications_service as AppsService
from user_accounts.models import Organization


def prebuild_newapps_pdf_for_san_francisco():
    """Gets or creates a NewAppsPDF for San Francisco
        links it to all the unread applications
        and rebuilds the PDF
    """
    sf_pubdef = Organization.objects.get(slug='sf_pubdef')
    # get or create the NewAppsPDF
    newapps_pdf = models.NewAppsPDF.objects.filter(
        organization_id=sf_pubdef.id).first()
    if not newapps_pdf:
        newapps_pdf = models.NewAppsPDF(
            organization_id=sf_pubdef.id)
        # get the unread apps
    unread_apps = AppsService.get_unread_applications_for_org(sf_pubdef)
    unread_app_ids = [app.id for app in unread_apps]
    unread_apps_without_pdfs = models.Application.objects.annotate(
        filled_pdf_count=Count('form_submission')
    ).filter(id__in=unread_app_ids, filled_pdf_count=0)
    # build individual filled pdfs if necessary
    for app in unread_apps_without_pdfs:
        fill_pdf_for_application(app.id)
    # get all the filled PDFs and join them to create the group pdf
    filled_pdfs = models.FilledPDF.objects.filter(
        submission__applications__id__in=unread_app_ids)
    newapps_pdf.set_bytes(
        models.get_parser().join_pdfs(
            filled.pdf for filled in filled_pdfs))
    newapps_pdf.save()
    # link unread apps
    newapps_pdf.applications.add(*unread_apps)
    return newapps_pdf


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
