import time
from behave import given, when, then
from intake.tests import factories, mock
from intake.constants import PACIFIC_TIME
from user_accounts.models import Organization
from intake.models import FormSubmission
from user_accounts.tests.factories import UserProfileFactory
from selenium.common.exceptions import NoSuchElementException

SEARCHABLE_APPLICANT_ID = None
application_row_selector = 'tr.application-listing[data-key="{}"]'
followup_row_selector = 'tr.form_submission[data-key="{}"]'


@given('"{count}" applications')
@given('"{count}" applications to "{org_slug}"')
@given('"{count}" "{status}" applications to "{org_slug}"')
def create_fake_applications(context, count, org_slug=None, status=None):
    count = int(count)
    if org_slug:
        org = Organization.objects.get(slug=org_slug)
        factories.FormSubmissionWithOrgsFactory.create_batch(
            count, organizations=[org])
        if status:
            for sub in FormSubmission.objects.all():
                app = sub.applications.first()
                app.has_been_opened = True
                app.save()
            if status == "read and updated":
                profile = UserProfileFactory(organization=org)
                for sub in FormSubmission.objects.all():
                    factories.StatusUpdateFactory(
                        application=sub.applications.first(),
                        author=profile.user)

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
    search_input = context.browser.find_element_by_css_selector(
        'input[name="q"]')
    search_input.send_keys('Waldini')
    time.sleep(1)


@when("I click on the applicant's row")
def click_row(context):
    selector = application_row_selector.format(SEARCHABLE_APPLICANT_ID)
    selector += ' > td:first-child > a'
    element = context.browser.find_element_by_css_selector(selector)
    element.click()


@then("I should not see the applicant listed")
def does_not_show_application_row(context):
    selector = application_row_selector.format(SEARCHABLE_APPLICANT_ID)
    with context.test.assertRaises(NoSuchElementException):
        context.browser.find_element_by_css_selector(selector)


@then("I should see the applicant's followup row")
def shows_followup_row(context):
    selector = followup_row_selector.format(SEARCHABLE_APPLICANT_ID)
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
    row_selector = followup_row_selector.format(SEARCHABLE_APPLICANT_ID)
    note_form_selector = 'form.note-create_form'
    button_selector = ' '.join([
        row_selector, note_form_selector, 'button[type="submit"]'])
    element = context.browser.find_element_by_css_selector(button_selector)
    context.test.assertIn('Save note', element.text)


@when("I add a note about the applicant's case")
def create_note(context):
    row_selector = followup_row_selector.format(SEARCHABLE_APPLICANT_ID)
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
    row_selector = followup_row_selector.format(SEARCHABLE_APPLICANT_ID)
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
    step_text = 'Then it should load "application/{}/"'\
        .format(SEARCHABLE_APPLICANT_ID)
    context.execute_steps(step_text)


@then('I should see "{count}" in the active tab')
def count_appears_in_tab(context, count):
    selector = "div.app-index-nav-bar > ul > li.active > a"
    element = context.browser.find_element_by_css_selector(selector)
    context.test.assertIn(count, element.text)


@then(
    'I should see "{count}" applications in the table when that tab is active')
def correct_number_of_rows_returned(context, count):
    listed_class = "application-listing"
    elements = context.browser.find_elements_by_class_name(listed_class)
    context.test.assertEqual(int(count), len(elements))


@then('I should see the Print All button')
def print_all_button_visible(context):
    selector = "a.print-all"
    element = context.browser.find_element_by_css_selector(selector)
    context.test.assertIn("Print All", element.text)


@then('I should not see the Print All button')
def print_all_button_not_visible(context):
    selector = "a.print-all"
    with context.test.assertRaises(NoSuchElementException):
        element = context.browser.find_element_by_css_selector(selector)
