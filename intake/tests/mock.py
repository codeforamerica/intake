import uuid
import os
import factory
from pytz import timezone
from faker import Factory as FakerFactory
from django.core.files import File
from django.utils.datastructures import MultiValueDict

from intake import models
from unittest.mock import Mock
Pacific = timezone('US/Pacific')

fake = FakerFactory.create('en_US', includes=['intake.tests.mock_county_forms'])

RAW_FORM_DATA = MultiValueDict({
    'address.city': [''],
    'address.state': ['CA'],
    'address.street': [''],
    'address.zip': [''],
    'dob.day': [''],
    'dob.month': [''],
    'dob.year': [''],
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
})

NEW_RAW_FORM_DATA = {
    'address.city': '',
    'address.state': 'CA',
    'address.street': '',
    'address.zip': '',
    'contact_preferences': ['prefers_email'],
    'dob.day': '',
    'dob.month': '',
    'dob.year': '',
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


PDF_FILLABLE_DATA = {
    'Address City': 'Oakland',
    'Address State': 'CA',
    'Address Street': '111 Main St.',
    'Address Zip': '94609',
    'Arrested outside SF': 'Yes',
    'Cell phone number': '510-415-0000',
    'Charged with a crime': 'No',
    'DOB': '2/1/82',
    'Date': '6/11/2016',
    'Date of Birth': '2/1/82',
    'Dates arrested outside SF': '2004',
    'Email Address': 'someone@gmail.com',
    'Employed': 'Yes',
    'First Name': 'Foo',
    'FirstName': 'Foo',
    'Home phone number': '',
    'How did you hear about the Clean Slate Program': 'A friend',
    'If probation where and when?': 'contra costa 2017',
    'Last Name': 'Bar',
    'LastName': 'Bar',
    'MI': 'G',
    'May we leave voicemail': 'Off',
    'May we send mail here': 'Off',
    'Monthly expenses': '1800',
    'On probation or parole': 'Yes',
    'Other phone number': '',
    'SSN': 'SS# 999-99-9999',
    'Serving a sentence': 'No',
    'Social Security Number': '999-99-9999',
    'US Citizen': 'Yes',
    'What is your monthly income': '1800',
    'Work phone number': ''}

def pdf_fillable_models():
    new_model_for_pdf = Mock(
        answers=dict(
            contact_preferences=['prefers_email', 'prefers_sms', 'prefers_snailmail'],
            address=dict(
                street='111 Main St.',
                city='Oakland',
                state='CA',
                zip='94609'),
            rap_outside_sf='yes',
            phone_number='510-415-0000',
            being_charged='no',
            dob=dict(month='2', day='1', year='82'),
            when_where_outside_sf='2004',
            email='someone@gmail.com',
            currently_employed='yes',
            first_name='Foo',
            middle_name='Gaz',
            last_name='Bar',
            how_did_you_hear='A friend',
            on_probation_parole='yes',
            where_probation_or_parole='contra costa',
            when_probation_or_parole='2017',
            monthly_income='1800',
            monthly_expenses='1800',
            ssn='999999999',
            us_citizen='yes',
            serving_sentence='no',
            ))

    old_model_for_pdf = Mock(
        answers=dict(
            contact_preferences=[
                'prefers_email', 'prefers_sms', 'prefers_snailmail'],
            address_street='111 Main St.',
            address_city='Oakland',
            address_state='CA',
            address_zip='94609',
            rap_outside_sf='yes',
            phone_number='510-415-0000',
            being_charged='no',
            dob_month='2',
            dob_day='1',
            dob_year='82',
            when_where_outside_sf='2004',
            email='someone@gmail.com',
            currently_employed='yes',
            first_name='Foo',
            middle_name='Gaz',
            last_name='Bar',
            how_did_you_hear='A friend',
            on_probation_parole='yes',
            where_probation_or_parole='contra costa',
            when_probation_or_parole='2017',
            monthly_income='1800',
            monthly_expenses='1800',
            ssn='999999999',
            us_citizen='yes',
            serving_sentence='no',
            ))
    for model in [old_model_for_pdf, new_model_for_pdf]:
        model.get_local_date_received.return_value = '6/11/2016'

    return old_model_for_pdf, new_model_for_pdf


def post_data(**kwargs):
    for key, value in kwargs.items():
        if isinstance(value, str):
            kwargs[key] = [value] 
    return MultiValueDict(kwargs)

def form_answers(**kwargs):
    data = fake.sf_county_form_answers(**kwargs)
    return post_data(**data)

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
        lambda: fake.cleaned_sf_county_form_answers())

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

def useable_pdf():
    example_pdf = File(open(os.environ.get('TEST_PDF_PATH'), 'rb'))
    return FillablePDFFactory.create(
            name="Clean Slate",
            pdf=example_pdf,
            translator = "intake.translators.clean_slate.translator"
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

