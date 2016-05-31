import factory
from faker import Factory as FakerFactory
from django.core.files import File
from pytz import timezone

from intake import models

fake = FakerFactory.create('en_US', includes=['intake.tests.mock_county_forms'])
Pacific = timezone('US/Pacific')


def local(datetime):
    return Pacific.localize(datetime)


class FormSubmissionFactory(factory.DjangoModelFactory):
    date_received = factory.LazyFunction(
        lambda: local(fake.date_time_between('-2w', 'now')))
    answers = factory.LazyFunction(
        lambda: fake.sf_county_form_answers())

    class Meta:
        model = models.FormSubmission


class FillablePDFFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.FillablePDF


def fillable_pdf():
    return FillablePDFFactory.create(
            name = "Sample PDF",
            pdf = File(open(
                'tests/sample_pdfs/sample_form.pdf', 'rb')),
            translator = "tests.sample_translator.translate"
        )