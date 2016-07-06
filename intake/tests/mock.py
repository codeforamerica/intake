import uuid
import factory
from faker import Factory as FakerFactory
from django.core.files import File
from pytz import timezone

from intake import models
from unittest.mock import Mock

fake = FakerFactory.create('en_US', includes=['intake.tests.mock_county_forms'])
Pacific = timezone('US/Pacific')

RAW_FORM_DATA = {
    'address_city': [''],
    'address_state': ['CA'],
    'address_street': [''],
    'address_zip': [''],
    'dob_day': [''],
    'dob_month': [''],
    'dob_year': [''],
    'drivers_license_number': [''],
    'email': [''],
    'first_name': [''],
    'how_did_you_hear': [''],
    'last_name': [''],
    'middle_name': [''],
    'monthly_expenses': [''],
    'monthly_income': [''],
    'phone_number': [''],
    'ssn': [''],
    'when_probation_or_parole': [''],
    'when_where_outside_sf': [''],
    'where_probation_or_parole': ['']
}

NEW_RAW_FORM_DATA = {
    'address_city': '',
    'address_state': 'CA',
    'address_street': '',
    'address_zip': '',
    'contact_preferences': ['prefers_email'],
    'dob_day': '',
    'dob_month': '',
    'dob_year': '',
    'email': 'foo@bar.com',
    'first_name': 'Foo',
    'how_did_you_hear': '',
    'last_name': 'Bar',
    'middle_name': '',
    'monthly_expenses': '',
    'monthly_income': '',
    'phone_number': '',
    'ssn': '',
    'when_probation_or_parole': '',
    'when_where_outside_sf': '',
    'where_probation_or_parole': '',
}



def local(datetime):
    return Pacific.localize(datetime)

def uuids(count):
    return [uuid.uuid4().hex for i in range(count)]

def fake_typeseam_submission_dicts(uuids):
    return [{
        'uuid': uuid,
        'date_received': fake.date_time_between('-2w', 'now'),
        'answers': fake.sf_county_form_answers()
        } for uuid in uuids]


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

