import random
from faker import Faker
# first, import a similar Provider or use the default one
from faker.providers import BaseProvider

from intake.constants import GENDER_PRONOUN_CHOICES

# create new provider class


class Provider(BaseProvider):

    def some_choice(self, choices):
        return random.choice(
            [key for key, display in choices])

    def maybe(self, chance_of_yes=0.5):
        return self.random_element({
            "yes": chance_of_yes,
            "no": 1.0 - chance_of_yes})

    def generate_contact_preferences(self):
        preferences = random.randint(1,4)
        return random.sample([ 
            'prefers_email',
            'prefers_sms',
            'prefers_snailmail',
            'prefers_voicemail',
            ], preferences)

    def sf_county_form_answers(self, **overrides):
        data = {
            'first_name': self.generator.first_name(),
            'middle_name': self.generator.first_name(),
            'last_name': self.generator.last_name(),
            'contact_preferences': self.generate_contact_preferences(),
            'phone_number': self.numerify('###-###-####'),
            'email': self.generator.free_email(),
            'address.street': self.generator.street_address(),
            'address.city': self.generator.city(),
            'address.state': self.generator.state_abbr(),
            'address.zip': self.generator.zipcode(),
            'being_charged': self.maybe(0.05),
            'currently_employed': self.maybe(0.4),
            'dob.day': str(random.randint(1, 31)),
            'dob.month': str(random.randint(1, 12)),
            'dob.year': str(random.randint(1959, 2000)),
            'monthly_expenses': str(random.randint(0, 3000)),
            'monthly_income': str(random.randint(0, 7000)),
            'rap_outside_sf': self.maybe(0.1),
            'serving_sentence': self.maybe(0.05),
            'ssn': self.numerify('#########'),
            'us_citizen': self.maybe(0.8),
            'on_probation_parole': self.maybe(0.1),
            'when_probation_or_parole': '',
            'when_where_outside_sf': '',
            'where_probation_or_parole': '',
            'how_did_you_hear': '',
            'additional_information': 'I want help',
        }
        data.update(overrides)
        return data

    def contra_costa_county_form_answers(self, **overrides):
        data = {
            'contact_preferences': self.generate_contact_preferences(),
            'first_name': self.generator.first_name(),
            'last_name': self.generator.last_name(),
            'phone_number': self.numerify('###-###-####'),
            'email': self.generator.free_email(),
            'dob.day': str(random.randint(1, 31)),
            'dob.month': str(random.randint(1, 12)),
            'dob.year': str(random.randint(1959, 2000)),
            'us_citizen': self.maybe(0.8),
            'address.street': self.generator.street_address(),
            'address.city': self.generator.city(),
            'address.state': self.generator.state_abbr(),
            'address.zip': self.generator.zipcode(),
            'on_probation_parole': self.maybe(0.1),
            'serving_sentence': self.maybe(0.05),
            'currently_employed': self.maybe(0.4),
            'monthly_income': str(random.randint(0, 7000)),
            'monthly_expenses': str(random.randint(0, 3000)),
            'income_source': 'a job',
            'how_did_you_hear': '',
            'additional_information': '',
        }
        data.update(overrides)
        return data

    def alameda_county_form_answers(self, **overrides):
        data = {
            'contact_preferences': self.generate_contact_preferences(),
            # 'preferred_pronouns': self.some_choice(GENDER_PRONOUN_CHOICES),
            'first_name': self.generator.first_name(),
            'middle_name': self.generator.first_name(),
            'last_name': self.generator.last_name(),
            'phone_number': self.numerify('###-###-####'),
            'alternate_phone_number': self.numerify('###-###-####'),
            'email': self.generator.free_email(),
            'dob.day': str(random.randint(1, 31)),
            'dob.month': str(random.randint(1, 12)),
            'dob.year': str(random.randint(1959, 2000)),
            'us_citizen': self.maybe(0.8),
            'address.street': self.generator.street_address(),
            'address.city': self.generator.city(),
            'address.state': self.generator.state_abbr(),
            'address.zip': self.generator.zipcode(),
            'on_probation_parole': 'yes',
            'finished_half_probation': 'not_applicable',
            'reduced_probation': 'not_applicable',
            'being_charged': self.maybe(0.05),
            'serving_sentence': self.maybe(0.05),
            'has_suspended_license': self.maybe(0.3),
            'owes_court_fees': self.maybe(0.4),
            'monthly_income': str(random.randint(0, 7000)),
            'on_public_benefits': self.maybe(0.7),
            'owns_home': self.maybe(0.1),
            'household_size': str(random.randint(0, 4)),
            'how_did_you_hear': 'from work',
            'additional_information': 'I want help',
        }
        data.update(overrides)
        return data

    def declaration_letter_answers(self, **overrides):
        data = {
            'declaration_letter_intro': self.generator.paragraph(4, True),
            'declaration_letter_life_changes': self.generator.paragraph(
                4, True),
            'declaration_letter_activities': self.generator.paragraph(4, True),
            'declaration_letter_goals': self.generator.paragraph(4, True),
            'declaration_letter_why': self.generator.paragraph(4, True),
        }
        data.update(overrides)
        return data

    def other_county_answers(self, **overrides):
        data = {
            'contact_preferences': self.generate_contact_preferences(),
            'first_name': self.generator.first_name(),
            'phone_number': self.numerify('###-###-####'),
            'email': self.generator.free_email(),
            'address.street': self.generator.street_address(),
            'address.city': self.generator.city(),
            'address.state': self.generator.state_abbr(),
            'address.zip': self.generator.zipcode(),
            'how_did_you_hear': '',
        }
        data.update(overrides)
        return data

    def cleaned_sf_county_form_answers(self, **overrides):
        data = {
            'first_name': self.generator.first_name(),
            'middle_name': self.generator.first_name(),
            'last_name': self.generator.last_name(),
            'contact_preferences': self.generate_contact_preferences(),
            'phone_number': self.numerify('###-###-####'),
            'email': self.generator.free_email(),
            'address': {
                'street': self.generator.street_address(),
                'city': self.generator.city(),
                'state': self.generator.state_abbr(),
                'zip': self.generator.zipcode(),
            },
            'being_charged': self.maybe(0.05),
            'currently_employed': self.maybe(0.4),
            'dob': {
                'day': str(random.randint(1, 31)),
                'month': str(random.randint(1, 12)),
                'year': str(random.randint(1959, 2000)),
            },
            'monthly_expenses': str(random.randint(0, 3000)),
            'monthly_income': str(random.randint(0, 7000)),
            'rap_outside_sf': self.maybe(0.1),
            'serving_sentence': self.maybe(0.05),
            'ssn': self.numerify('#########'),
            'us_citizen': self.maybe(0.8),
            'on_probation_parole': self.maybe(0.1),
            'when_probation_or_parole': '',
            'when_where_outside_sf': '',
            'where_probation_or_parole': '',
            'how_did_you_hear': '',
            'additional_information': 'I want help',
        }
        data.update(overrides)
        return data

    def ebclc_answers(self, **overrides):
        data = self.alameda_county_form_answers(**overrides)
        data['monthly_income'] = 3001
        data['owns_home'] = "yes"
        return data

    def alameda_pubdef_answers(self, **overrides):
        data = self.alameda_county_form_answers(**overrides)
        data['monthly_income'] = 2999
        data['owns_home'] = "no"
        return data

    def all_county_answers(self, **overrides):
        data = {
            **self.sf_county_form_answers(),
            **self.alameda_county_form_answers(),
            **self.contra_costa_county_form_answers()
        }
        data.update(overrides)
        return data