from behave import then, given
from intake import models
from intake.services import pdf_service
from intake.tests import factories
from user_accounts.models import Organization
from features.steps.language_hacks import oxford_comma_text_to_list


@given('a fillable PDF for "{county_slug}"')
def preload_fillablepdf(context, county_slug):
    org = Organization.objects.get(slug=county_slug)
    factories.FillablePDFFactory(organization=org)


@then('it should have a FilledPDF')
def test_has_filledpdf(context):
    filled_pdf = models.FilledPDF.objects.first()
    context.test.assertTrue(filled_pdf, "no filled PDF here")


@then('there should be a pre-filled PDF for "{applicant_name}"')
def test_prefilled_pdf_for_applicant(context, applicant_name):
    first_name, last_name = applicant_name.split(' ')
    sub = models.FormSubmission.objects.filter(
        first_name=first_name, last_name=last_name).first()
    context.test.assertTrue(sub.filled_pdfs.count() >= 1)


@then(
    'there should be a prebuilt PDF bundle for "{applicant_names}" to '
    '"{org_slug}"')
def test_applicant_in_prebuilt_pdf_for_org(context, applicant_names, org_slug):
    applicant_names = oxford_comma_text_to_list(applicant_names)
    app_ids = []
    for applicant_name in applicant_names:
        first_name, last_name = applicant_name.split(' ')
        app_ids.append(
            models.Application.objects.filter(
                form_submission__first_name=first_name,
                form_submission__last_name=last_name,
                organization__slug=org_slug).first().id)
    prebuilt = pdf_service.get_prebuilt_pdf_bundle_for_app_id_set(app_ids)
    context.test.assertTrue(prebuilt)


@then('there should not be a prebuilt PDF for "{org_slug}"')
def test_no_newapps_pdf_for_org(context, org_slug):
    context.test.assertFalse(
        models.PrebuiltPDFBundle.objects.filter(
            organization__slug=org_slug).exists())
