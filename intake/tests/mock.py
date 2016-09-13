import uuid
import os
import factory
import random
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

def build_seed_submissions():
    from user_accounts.models import Organization
    from formation.forms import county_form_selector
    orgs = Organization.objects.all()
    counties = list(models.County.objects.all())
    answer_pairs = {
        'sf_pubdef': fake.sf_county_form_answers,
        'cc_pubdef': fake.contra_costa_county_form_answers,
        'ebclc': fake.ebclc_answers,
        'a_pubdef': fake.alameda_pubdef_answers
    }
    form_pairs = {
        'sf_pubdef': county_form_selector.get_combined_form_class(
            counties=['sanfrancisco']),
        'cc_pubdef': county_form_selector.get_combined_form_class(
            counties=['contracosta']),
        'ebclc': county_form_selector.get_combined_form_class(
            counties=['alameda']),
        'a_pubdef': county_form_selector.get_combined_form_class(
            counties=['alameda'])
    }
    subs = []
    for org in orgs:
        if org.slug in answer_pairs:
            for i in range(4):
                answers = answer_pairs[org.slug]()
                Form = form_pairs[org.slug]
                form = Form(answers)
                form.is_valid()
                sub = models.FormSubmission.create_for_organizations(
                    organizations=[org],
                    answers=form.cleaned_data)
                subs.append(sub)
    # make combos
    for i in range(6):
        num_counties = random.randint(2, 3)
        answers = fake.all_county_answers()
        these_counties = random.sample(counties, num_counties)
        Form = county_form_selector.get_combined_form_class(
            counties=[c.slug for c in these_counties])
        form = Form(answers)
        form.is_valid()
        sub = models.FormSubmission.create_for_counties(
            counties=these_counties,
            answers=form.cleaned_data)
        subs.append(sub)

    read_subs = random.sample(subs, 5)
    for sub in read_subs:
        org_user = sub.organizations.first().profiles.first().user
        models.ApplicationLogEntry.log_opened(
            [sub.id], org_user)
    # make bundles
    from intake.submission_bundler import SubmissionBundler
    bundler = SubmissionBundler()
    bundler.map_submissions_to_orgs()
    for bundle in bundler.organization_bundle_map.values():
        bundle.create_app_bundle()
    return subs