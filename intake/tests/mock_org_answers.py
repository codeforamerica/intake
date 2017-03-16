from faker import Factory as FakerFactory

fake = FakerFactory.create(
    'en_US', includes=['intake.tests.mock_county_forms'])

answer_lookup = {}


class AnswerGenerator:
    def __init__(self, mock_method_name, form_class):
        self.mock_method_name = mock_method_name
        self.form_class = form_class

    def __call__(self):
        raw_answers = getattr(fake, self.mock_method_name)()
        form = self.form_class(raw_answers, validate=True)
        return form.cleaned_data


def populate_answer_lookup():
    from user_accounts.models import Organization
    from formation.forms import county_form_selector
    for org in Organization.objects.filter(is_receiving_agency=True):
        answer_mock_method_name = org.slug + '_answers'
        if not hasattr(fake, answer_mock_method_name):
            raise AttributeError(
                'There is no mock form answers method for {}'.format(org.slug))
        form_class = county_form_selector.get_combined_form_class(
                counties=[org.county.slug])
        answer_lookup[org.slug] = AnswerGenerator(
            answer_mock_method_name, form_class)


def get_answers_for_org(org_slug):
    if org_slug not in answer_lookup:
        populate_answer_lookup()
    return answer_lookup[org_slug]()


def get_answers_for_orgs(*slugs):
    answers = {}
    for slug in slugs:
        answers.update(**get_answers_for_org(slug))
    return answers
