from behave import given, when, then
from intake.tests import factories, mock
import time

SEARCHABLE_APPLICANT_ID = None
application_row_selector = 'tr.form_submission[data-key="{}"]'


@given('"{}" applications')
def create_fake_applications(context, count):
    count = int(count)
    factories.FormSubmissionWithOrgsFactory.create_batch(count)


@given('an applicant to search for')
def create_searchable_applicant(context):
    global SEARCHABLE_APPLICANT_ID
    answers = mock.fake.contra_costa_county_form_answers(
        first_name='Waldo',
        last_name='Waldini',
        phone_number='5555555555',
        email='waldo@odlaw.institute'
        )
    sub = factories.FormSubmissionWithOrgsFactory(
        answers=answers,
        date_received=mock.fake.date_time_between('-4w', '-2w'))
    SEARCHABLE_APPLICANT_ID = sub.id


@when("I search for the applicant's name")
def search_by_name(context):
    search_input_selector = 'form.search_form input[name="q"]'
    search_input = context.browser.find_element_by_css_selector(
        search_input_selector)
    search_input.send_keys('Waldini')


@then("I should see the applicant's followup row")
def shows_row(context):
    selector = application_row_selector.format(SEARCHABLE_APPLICANT_ID)
    element = context.browser.find_element_by_css_selector(selector)
    context.test.assertIn('Waldo', element.text)
    context.test.assertIn('Waldini', element.text)


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
    time.sleep(0.5)


@then('the note should be visible')
def note_is_visible(context):
    row_selector = application_row_selector.format(SEARCHABLE_APPLICANT_ID)
    element = context.browser.find_element_by_css_selector(
        ' '.join([row_selector, '.notes > .note:first-child']))
    context.test.assertIn('We found Waldo', element.text)
