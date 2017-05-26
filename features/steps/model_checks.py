from behave import then
from intake import models


@then('it should have a FilledPDF')
def test_has_filledpdf(context):
    fillable_pdf = models.FillablePDF.objects.all()
    filled_pdf = models.FilledPDF.objects.first()
    context.test.assertEqual(len(fillable_pdf), 1)
    context.test.assertTrue(filled_pdf, "no filled PDF here")
    # context.test.assertTrue(filled_pdf.pdf)
    # context.test.assertNotEqual(filled_pdf.pdf.size, 0)
