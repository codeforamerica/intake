from behave import when, then


def get_first_followup_row(context):
    """A helper function used by different steps
    """
    selector = '.followups tr.form_submission'
    rows = context.browser.find_elements_by_css_selector(selector)
    return rows[0]


@when('I add a note on the first application that says')
def add_note_to_first_followup_row(context):
    phrase = context.text.strip()
    row = get_first_followup_row(context)
    note_input = row.find_element_by_css_selector(
        '.note-create_form input[name=body]')
    note_input.send_keys(phrase)
    note_submit_button = row.find_element_by_css_selector(
        '.note-create_form button[type=submit]')
    note_submit_button.click()


@when('I add a "{tag_name}" tag on the first application')
def add_tag_to_first_followup_row(context, tag_name):
    row = get_first_followup_row(context)
    tags_input = row.find_element_by_css_selector(
        '.tags-add_tags input[name=tags]')
    tags_input.send_keys(tag_name)
    tags_submit_button = row.find_element_by_css_selector(
        '.tags-add_tags button[type=submit]')
    tags_submit_button.click()


@then('the notes on the first application should include')
def test_first_followup_row_notes_contain(context):
    phrase = context.text.strip()
    row = get_first_followup_row(context)
    notes = row.find_element_by_css_selector('.notes')
    context.test.assertIn(phrase, notes.text)


@then('the tags on the first application should include "{tag_name}"')
def test_first_followup_row_tags_include(context, tag_name):
    row = get_first_followup_row(context)
    tags = row.find_element_by_css_selector('.tags')
    context.test.assertIn(tag_name, tags.text)
