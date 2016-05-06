import random
import factory
from faker import Factory as FakerFactory
from factory.django import DjangoModelFactory

from intake import models as intake_models

fake = FakerFactory.create('en_US')


def lazy(func):
    return factory.LazyAttribute(func)


def maybe(chance_of_yes=0.5):
    return fake.random_element({
        "yes": chance_of_yes,
        "no": 1.0 - chance_of_yes})


def generate_answers():
    return {
            'prefers_email': maybe(0.2),
            'prefers_sms': maybe(0.7),
            'prefers_snailmail': maybe(0.02),
            'prefers_voicemail': maybe(0.3),
            'first_name': fake.first_name(),
            'middle_name': fake.first_name(),
            'last_name': fake.last_name(),
            'phone_number': fake.numerify('###-###-####'),
            'email': fake.free_email(),
            'address_street': fake.street_address(),
            'address_city': fake.city(),
            'address_state': fake.state_abbr(),
            'address_zip': fake.zipcode(),
            'being_charged': maybe(0.05),
            'currently_employed': maybe(0.4),
            'dob_day': str(random.randint(1,31)),
            'dob_month': str(random.randint(1,12)),
            'dob_year': str(random.randint(1959, 2000)),
            'monthly_expenses': str(random.randint(0, 3000)),
            'monthly_income': str(random.randint(0, 7000)),
            'rap_outside_sf': maybe(0.1),
            'serving_sentence': maybe(0.05),
            'ssn': fake.numerify('#########'),
            'us_citizen': maybe(0.8),
            'on_probation_parole': maybe(0.1),
            'when_probation_or_parole': '',
            'when_where_outside_sf': '',
            'where_probation_or_parole': '',
            'how_did_you_hear': '',
            } 


class FormSubmissionFactory(DjangoModelFactory):
    date_received = lazy(lambda m: fake.date_time_between('-2w'))
    answers = lazy(lambda m: generate_answers())

    class Meta:
        model = intake_models.FormSubmission
