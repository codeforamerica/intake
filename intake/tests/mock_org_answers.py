from unittest.mock import patch
from faker import Factory as FakerFactory

fake = FakerFactory.create(
    'en_US', includes=['intake.tests.mock_county_forms'])

answer_lookup = {}


class AnswerGenerator:

    def __init__(self, mock_method_form_class_pairs):
        self.mock_method_form_class_pairs = mock_method_form_class_pairs

    def __call__(self):
        cleaned_data = {}
        for mock_method_name, form_class in \
                self.mock_method_form_class_pairs.items():
            raw_answers = getattr(fake, mock_method_name)()
            # don't acutally validate, just parse. We are generating seed data
            form = form_class(
                raw_answers, validate=True, skip_validation_parse_only=True)
            cleaned_data.update(form.cleaned_data)
        return cleaned_data


def populate_answer_lookup():
    from user_accounts.models import Organization
    from formation.forms import county_form_selector, DeclarationLetterFormSpec
    letter_form_class = DeclarationLetterFormSpec().build_form_class()
    for org in Organization.objects.filter(is_receiving_agency=True):
        answer_mock_method_name = org.slug + '_answers'
        if not hasattr(fake, answer_mock_method_name):
            raise AttributeError(
                'There is no mock form answers method for {}'.format(org.slug))
        form_class = county_form_selector.get_combined_form_class(
            counties=[org.county.slug])
        mock_method_form_pairs = {}
        mock_method_form_pairs[answer_mock_method_name] = form_class
        if org.requires_declaration_letter:
            mock_method_form_pairs.update(
                declaration_letter_answers=letter_form_class)
        answer_lookup[org.slug] = AnswerGenerator(mock_method_form_pairs)


def get_answers_for_org(organization, **overrides):
    if organization.slug not in answer_lookup:
        populate_answer_lookup()
    answers = answer_lookup[organization.slug]()
    answers.update(**overrides)
    return answers


def get_answers_for_orgs(organizations, **overrides):
    answers = {}
    for organization in organizations:
        answers.update(**get_answers_for_org(organization, **overrides))
    return answers
