import uuid
import os
import factory
from pytz import timezone
from faker import Factory as FakerFactory
from django.core.files import File
from django.core.management import call_command
from django.conf import settings
from django.utils.datastructures import MultiValueDict

from intake import models
from user_accounts.tests.mock import OrganizationFactory
from unittest.mock import Mock
Pacific = timezone('US/Pacific')

fake = FakerFactory.create(
    'en_US', includes=['intake.tests.mock_county_forms'])

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
    'address.state': '',
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


def load_counties_and_orgs():
    fixtures = ['counties', 'organizations']
    call_command('loaddata', *fixtures)


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

    @factory.post_generation
    def organizations(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.organizations.add(*[
                organization.id for organization in extracted
            ])

    @classmethod
    def create(cls, *args, **kwargs):
        if 'organizations' not in kwargs:
            kwargs['organizations'] = OrganizationFactory.sample()
        return super().create(*args, **kwargs)


class FillablePDFFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.FillablePDF


def fillable_pdf(**kwargs):
    attributes = dict(
        name="Sample PDF",
        pdf=File(open(
            'tests/sample_pdfs/sample_form.pdf', 'rb')),
        translator="tests.sample_translator.translate",
    )
    attributes.update(kwargs)
    return FillablePDFFactory.create(**attributes)


def useable_pdf(org):
    path = getattr(settings, 'TEST_PDF_PATH', os.environ.get('TEST_PDF_PATH'))
    example_pdf = File(open(path, 'rb'))
    return FillablePDFFactory.create(
        name="Clean Slate",
        pdf=example_pdf,
        translator="intake.translators.clean_slate.translator",
        organization=org,
    )


class FrontSendMessageResponse:
    SUCCESS_JSON = {'status': 'accepted'}
    ERROR_JSON = {'errors': [{'title': 'Bad request',
                              'detail': 'Body did not satisfy requirements',
                              'status': '400'}]}

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
