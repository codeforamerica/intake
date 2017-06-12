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
    fillable_pdf = models.FillablePDF.objects.all()
    filled_pdf = models.FilledPDF.objects.first()
    context.test.assertEqual(len(fillable_pdf), 1)
    context.test.assertTrue(filled_pdf, "no filled PDF here")
