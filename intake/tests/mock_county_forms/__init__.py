import random
from faker import Faker
# first, import a similar Provider or use the default one
from faker.providers import BaseProvider

# create new provider class
class Provider(BaseProvider):

    def maybe(self, chance_of_yes=0.5):
        return self.random_element({
            "yes": chance_of_yes,
            "no": 1.0 - chance_of_yes})

    def generate_contact_preferences(self):
        methods = {
            'prefers_email': self.maybe(0.2),
            'prefers_sms': self.maybe(0.7),
            'prefers_snailmail': self.maybe(0.02),
            'prefers_voicemail': self.maybe(0.3),
        }
        return [k for k, v in methods.items() if v == 'yes']

    def sf_county_form_answers(self):
        return {
            'first_name': self.generator.first_name(),
            'middle_name': self.generator.first_name(),
            'last_name': self.generator.last_name(),
            'contact_preferences': self.generate_contact_preferences(),
            'phone_number': self.numerify('###-###-####'),
            'email': self.generator.free_email(),
            'address_street': self.generator.street_address(),
            'address_city': self.generator.city(),
            'address_state': self.generator.state_abbr(),
            'address_zip': self.generator.zipcode(),
            'being_charged': self.maybe(0.05),
            'currently_employed': self.maybe(0.4),
            'dob_day': str(random.randint(1,31)),
            'dob_month': str(random.randint(1,12)),
            'dob_year': str(random.randint(1959, 2000)),
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
            }
