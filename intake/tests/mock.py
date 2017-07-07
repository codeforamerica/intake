import uuid
import os
import random
import factory
import datetime as dt
from pytz import timezone
from faker import Factory as FakerFactory
from django.core.files import File
from django.core import serializers
from django.core.management import call_command
from django.conf import settings
from django.utils.datastructures import MultiValueDict
from user_accounts.models import Organization

from taggit.models import Tag

from intake import models, constants, services
from intake.constants import PACIFIC_TIME
from intake.tests import mock_user_agents, mock_referrers, factories
from intake.services import bundles as BundlesService
from user_accounts.models import Organization
from user_accounts.tests.mock import create_seed_users
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


def make_submission():
    return factories.FormSubmissionWithOrgsFactory.create()


def make_tag(name="example"):
    tag = Tag(name=name)
    tag.save()
    return tag


def make_note(user, submission_id):
    note = models.ApplicationNote(
        user=user,
        submission_id=submission_id,
        body="where is the mustard?",
    )
    note.save()
    return note


def get_old_date():
    return PACIFIC_TIME.localize(fake.date_time_between('-8w', '-5w'))


def get_newer_date():
    return PACIFIC_TIME.localize(fake.date_time_between('-3w', 'now'))


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


class FillablePDFFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.FillablePDF


def fillable_pdf(**kwargs):
    attributes = dict(
        name="Sample PDF",
        pdf=File(open(
            'tests/sample_pdfs/sample_form.pdf', 'rb')),
        translator="tests.sample_translator.translate",
        organization=Organization.objects.get(slug='sf_pubdef')
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


def fake_user_agent():
    return random.choice(mock_user_agents.choices)


def fake_referrer():
    return random.choice(mock_referrers.choices)


def completion_time(spread=9, shift=3):
    """Returns a random timedelta between 3 and 12 minutes
    """
    base = random.random()
    minutes = (base * spread) + shift
    return dt.timedelta(minutes=minutes)


def random_interpolate_minutes_between(timedelta, points=1, segment_limit=0.6):
    full_span = timedelta / dt.timedelta(minutes=1)  # minutes as float
    denominator = points + 1
    full_segment = full_span / denominator
    segment_length = full_segment * segment_limit
    starting_points = []
    resulting_points = []
    starting_point = 0.0
    for i in range(points):
        starting_point = starting_point + full_segment
        starting_points.append(starting_point)
    for starting_point in starting_points:
        shift = starting_point - (segment_length * 0.5)
        resulting_points.append(completion_time(segment_length, shift))
    return resulting_points


def fake_app_started(
        applicant, counties, referrer=None, ip=None, user_agent=None,
        time=None):
    if not referrer:
        referrer = fake_referrer()
    if not user_agent:
        user_agent = fake_user_agent()
    if not ip:
        ip = fake.ipv4()
    event = models.ApplicationEvent(
        name=models.ApplicationEvent.APPLICATION_STARTED,
        applicant_id=applicant.id,
        data=dict(
            counties=counties, referrer=referrer, ip=ip, user_agent=user_agent)
    )
    if time:
        event.time = time
    event.save()
    return event


def fake_page_complete(applicant, page_name, time=None):
    event = models.ApplicationEvent(
        name=models.ApplicationEvent.APPLICATION_PAGE_COMPLETE,
        applicant_id=applicant.id,
        data=dict(page_name=page_name))
    if time:
        event.time = time
    event.save()
    return event


def fake_app_submitted(applicant, time=None):
    event = models.ApplicationEvent(
        name=models.ApplicationEvent.APPLICATION_SUBMITTED,
        applicant_id=applicant.id,
        data=dict())
    if time:
        event.time = time
    event.save()
    return event


def make_mock_submission_event_sequence(applicant):
    sub = models.FormSubmission.objects.get(applicant_id=applicant.id)
    events = []
    time_to_complete = completion_time()
    sub_finish = sub.date_received
    start_time = sub_finish - time_to_complete
    page_sequences = [
        constants.PAGE_COMPLETE_SEQUENCES[org.slug]
        for org in sub.organizations.all()]
    counties = [org.county.slug for org in sub.organizations.all()]
    longest_sequence = max(page_sequences, key=lambda seq: len(seq))
    intermediate_pages = longest_sequence[1:-1]
    intermediate_times = [
        start_time + timeshift
        for timeshift in random_interpolate_minutes_between(
            time_to_complete, len(intermediate_pages))]
    times = [start_time, *intermediate_times, sub_finish]
    events.append(fake_app_started(applicant, counties, time=start_time))
    for time, page_name in zip(times, longest_sequence):
        events.append(fake_page_complete(applicant, page_name, time=time))
    events.append(fake_app_submitted(applicant, sub_finish))
    return events


def make_mock_transfer_sub(from_org, to_org):
    sub = factories.FormSubmissionWithOrgsFactory.create(
        organizations=[from_org])
    application = sub.applications.first()
    author = from_org.profiles.first().user
    # make a status_update prior to transfer
    factories.StatusUpdateWithNotificationFactory.create(
        application=application, author=author)
    transfer, *stuff = services.transfers_service.transfer_application(
        author=author, application=application,
        to_organization=to_org, reason="Transporter malfunction")
    message = 'Your case has been transferred to {}.\n{}'.format(
        to_org.name, to_org.short_confirmation_message)
    factories.StatusNotificationFactory.create(
        status_update=transfer.status_update, base_message=message,
        sent_message=message)
    return sub


def make_two_mock_transfers():
    orgs = Organization.objects.filter(can_transfer_applications=True)
    org_a = orgs[0]
    org_b = orgs[1]
    subs = []
    subs.append(make_mock_transfer_sub(org_a, org_b))
    subs.append(make_mock_transfer_sub(org_b, org_a))
    transfers = models.ApplicationTransfer.objects.filter(
        new_application__form_submission__in=subs)
    serialize_subs(
        subs, fixture_path('mock_2_transfers.json'), transfers)


def build_seed_submissions():
    subs = []
    orgs = Organization.objects.filter(is_receiving_agency=True)
    for org in orgs:
        # make 2 submissions to each org
        for i in range(2):
            sub = factories.FormSubmissionWithOrgsFactory.create(
                organizations=[org])
            subs.append(sub)
    # make 1 submission to multiple orgs
    target_orgs = Organization.objects.filter(
        is_receiving_agency=True).exclude(slug__contains='ebclc')
    multi_org_sub = factories.FormSubmissionWithOrgsFactory.create(
        organizations=target_orgs)
    subs.append(multi_org_sub)
    sub_ids = [sub.id for sub in subs]
    # applications = models.Application.objects.filter(
    #     form_submission_id__in=sub_ids)

    applicants = []
    for sub in subs:
        applicants.append(sub.applicant)

    """
    Creating status updates for all applications forces a mock situation
    in which there are 0 unread applications, which limits our test range.
    Working around that by only doing so for the first 2 applications to
    an org.
    """
    for org in orgs:
        updated_application = models.Application.objects.filter(
            organization=org, form_submission_id__in=sub_ids).first()
        factories.StatusUpdateWithNotificationFactory.create(
            application=updated_application,
            author=org.profiles.first().user)
        updated_application.has_been_opened = True
        updated_application.save()

    for org in orgs:
        org_subs = []
        for sub in subs:
            has_app = sub.applications.filter(organization=org).exists()
            if has_app and sub != multi_org_sub:
                org_subs.append(sub)
        # make a bundle for each org
        bundle = BundlesService.create_bundle_from_submissions(
            organization=org,
            submissions=org_subs,
            skip_pdf=True)
        # save bundle
        filename = 'mock_1_bundle_to_' + org.slug + ".json"
        dump_as_json([bundle], fixture_path(filename))
        filename = 'mock_{}_submissions_to_{}.json'.format(
            len(org_subs), org.slug)
        serialize_subs(org_subs, fixture_path(filename))
    serialize_subs(
        [multi_org_sub],
        fixture_path('mock_1_submission_to_multiple_orgs.json'))
    events = []
    for applicant in applicants:
        events.extend(
            make_mock_submission_event_sequence(applicant))
    dump_as_json(events, fixture_path('mock_application_events.json'))
    make_two_mock_transfers()


def fixture_path(filename):
    return os.path.join('intake', 'fixtures', filename)


def dump_as_json(objs, filepath):
    data = serializers.serialize(
        "json", objs, indent=2, use_natural_foreign_keys=True)
    with open(filepath, 'w') as f:
        f.write(data)


def serialize_subs(subs, filepath, *other_objects):
    applicants = [sub.applicant for sub in subs]
    visitors = [applicant.visitor for applicant in applicants]
    applications = models.Application.objects.filter(
        form_submission__in=subs)
    status_updates = []
    status_notifications = []
    status_updates = models.StatusUpdate.objects.filter(
        application__in=applications)
    status_notifications = models.StatusNotification.objects.filter(
        status_update__in=status_updates)
    with open(filepath, 'w') as f:
        data = [*visitors, *applicants, *subs, *applications,
                *status_updates, *status_notifications]
        for object_set in other_objects:
            data.extend(object_set)
        f.write(serializers.serialize(
            'json', data, indent=2, use_natural_foreign_keys=True))
