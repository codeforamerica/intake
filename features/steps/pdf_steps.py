from behave import then, given
from intake import models
from intake.tests import factories
from user_accounts.models import Organization


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


@then('"{applicant_name}" should be in the new apps PDF for "{org_slug}"')
def test_applicant_in_newapps_pdf_for_org(
        context, applicant_name, org_slug):
    first_name, last_name = applicant_name.split(' ')
    sub = models.FormSubmission.objects.filter(
        first_name=first_name, last_name=last_name).first()
    new_apps_pdf = models.NewAppsPDF.objects.filter(
        organization__slug=org_slug).first()
    sub_ids = new_apps_pdf.applications.values_list(
        'form_submission_id', flat=True)
    context.test.assertIn(sub.id, sub_ids)


@then('there should not be a new apps PDF for "{org_slug}"')
def test_no_newapps_pdf_for_org(context, org_slug):
    context.test.assertFalse(
        models.NewAppsPDF.objects.filter(
            organization__slug=org_slug).exists())
