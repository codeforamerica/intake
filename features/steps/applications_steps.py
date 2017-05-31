import time
from behave import given, when, then
from intake.tests import factories, mock
from intake.constants import PACIFIC_TIME
from user_accounts.models import Organization
from features.steps.web_loads_and_contains_steps import test_page_loads

SEARCHABLE_APPLICANT_ID = None
application_row_selector = 'tr.form_submission[data-key="{}"]'


@given('"{count}" applications')
@given('"{count}" applications to "{org_slug}"')
def create_fake_applications(context, count, org_slug=None):
    count = int(count)
    if org_slug:
        org = Organization.objects.get(slug=org_slug)
        factories.FormSubmissionWithOrgsFactory.create_batch(
            count, organizations=[org])
    else:
        factories.FormSubmissionWithOrgsFactory.create_batch(count)


@given('an applicant to search for')
@given('a "{org_slug}" application to search for')
def create_searchable_applicant(context, org_slug=None):
    global SEARCHABLE_APPLICANT_ID
    if org_slug:
        org = Organization.objects.get(slug=org_slug)
    answers = mock.fake.contra_costa_county_form_answers(
        first_name='Waldo',
        last_name='Waldini',
        phone_number='5555555555',
        email='waldo@odlaw.institute'
        )
    kwargs = dict(
        answers=answers,
        date_received=PACIFIC_TIME.localize(
            mock.fake.date_time_between('-4w', '-2w'))
        )
    if org_slug:
        kwargs.update(organizations=[org])
    sub = factories.FormSubmissionWithOrgsFactory(**kwargs)
    SEARCHABLE_APPLICANT_ID = sub.id


@when("I search for the applicant's name")
def search_by_name(context):
    search_input_selector = 'input[name="q"]'
    search_input = context.browser.find_element_by_css_selector(
        search_input_selector)
    search_input.send_keys('Waldini')
    time.sleep(0.4)


@then("I should see the applicant's followup row")
def shows_row(context):
    selector = application_row_selector.format(SEARCHABLE_APPLICANT_ID)
    element = context.browser.find_element_by_css_selector(selector)
    context.test.assertIn('Waldo', element.text)
    context.test.assertIn('Waldini', element.text)


@then("I should see the applicant's name in search results")
def shows_search_result_row(context):
    selector = 'ul.applications-autocomplete_results'
    element = context.browser.find_element_by_css_selector(selector)
    context.test.assertIn('Waldo Waldini', element.text)


@then('the create note form should be visible')
def has_note_input(context):
    row_selector = application_row_selector.format(SEARCHABLE_APPLICANT_ID)
    note_form_selector = 'form.note-create_form'
    button_selector = ' '.join([
        row_selector, note_form_selector, 'button[type="submit"]'])
    element = context.browser.find_element_by_css_selector(button_selector)
    context.test.assertIn('Save note', element.text)


@when("I add a note about the applicant's case")
def create_note(context):
    row_selector = application_row_selector.format(SEARCHABLE_APPLICANT_ID)
    note_form_selector = 'form.note-create_form'
    input_selector = ' '.join([
        row_selector, note_form_selector, 'input[name="body"'])
    input_elem = context.browser.find_element_by_css_selector(input_selector)
    input_elem.send_keys('We found Waldo')
    button_selector = ' '.join([
        row_selector, note_form_selector, 'button[type="submit"]'])
    button = context.browser.find_element_by_css_selector(button_selector)
    button.click()
    time.sleep(0.4)


@then('the note should be visible')
def note_is_visible(context):
    row_selector = application_row_selector.format(SEARCHABLE_APPLICANT_ID)
    element = context.browser.find_element_by_css_selector(
        ' '.join([row_selector, '.notes > .note:first-child']))
    context.test.assertIn('We found Waldo', element.text)


@when("I click on the applicant's search result")
def click_on_search_result(context):
    selector = ' '.join([
        'ul.applications-autocomplete_results', '>',
        'li.autocomplete-result:first-child', '>', 'a'])
    element = context.browser.find_element_by_css_selector(selector)
    element.click()


@then("it should load the applicant's detail page")
def test_detail_page_loads(context):
    test_page_loads(
        context, 'application/{}/'.format(SEARCHABLE_APPLICANT_ID))
