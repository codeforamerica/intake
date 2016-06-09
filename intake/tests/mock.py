import factory
from faker import Factory as FakerFactory
from django.core.files import File
from pytz import timezone

from intake import models
from unittest.mock import Mock

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

class FrontSendMessageResponse:
    SUCCESS_JSON = {'status': 'accepted'}
    ERROR_JSON = {'errors': [{'title': 'Bad request', 'detail': 'Body did not satisfy requirements', 'status': '400'}]}
    
    @classmethod
    def _make_response(cls, status_code, json):
        mock_response = Mock(status_code=status_code)
        mock_response.json.return_value = json
        return mock_response

    @classmethod
    def success(cls):
        return cls._make_response(202, cls.SUCCESS_JSON)

    @classmethod
    def error(cls):
        return cls._make_response(400, cls.ERROR_JSON)

