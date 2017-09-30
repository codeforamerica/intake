from behave import when


def fill_text_input(context, input_name, value):
    selector = 'input[name="{}"]'.format(input_name)
    element = context.browser.find_element_by_css_selector(selector)
    element.send_keys(value)


def click_submit_button(context, form_selector=''):
    selector = 'button[type="submit"]'
    if form_selector:
        selector = ' '.join([form_selector, selector])
    button = context.browser.find_element_by_css_selector(selector)
    button.click()


@when('"{checkbox_value}" is clicked on the "{checkbox_name}" radio button')
@when('the "{checkbox_name}" checkbox option "{checkbox_value}" is clicked')
def click_checkbox_choice(context, checkbox_name, checkbox_value):
    selector = "input[name='%s'][value='%s']" % (
        checkbox_name,
        checkbox_value,
    )
    checkbox = context.browser.find_element_by_css_selector(selector)
    checkbox.click()


@when('submit button in form "{form_class}" is clicked')
def click_submit(context, form_class):
    selector = "form.%s button[type='submit']" % (
        form_class,
    )
    checkbox = context.browser.find_element_by_css_selector(selector)
    checkbox.click()


@when('the "{input_name}" text input is set to "{value}"')
def type_in_text_input(context, input_name, value):
    selector = "input[name='%s'][type='text']" % (
        input_name,
    )
    text = context.browser.find_element_by_css_selector(selector)
    text.clear()
    text.send_keys(value)


@when('the "{input_name}" text area is set to "{value}"')
def type_in_textarea(context, input_name, value):
    selector = "textarea[name='%s']" % (
        input_name,
    )
    text = context.browser.find_element_by_css_selector(selector)
    text.clear()
    text.send_keys(value)


@when('the "{input_name}" email input is set to "{value}"')
def type_in_email_input(context, input_name, value):
    selector = "input[name='{}'][type='email']".format(input_name)
    text = context.browser.find_element_by_css_selector(selector)
    text.send_keys(value)


@when('I check "{checkbox_name}"')
def click_checkbox(context, checkbox_name):
    selector = "input[name='{}']".format(checkbox_name)
    checkbox = context.browser.find_element_by_css_selector(selector)
    checkbox.click()


@when('I click "{css_selector}"')
def click_element(context, css_selector):
    element = context.browser.find_element_by_css_selector(css_selector)
    element.click()


@when('I select the "{option_text}" option in "{select_name}"')
def double_click(context, option_text, select_name):
    selector = "select[name={}] option".format(select_name)
    option_elements = context.browser.find_elements_by_css_selector(selector)
    selected_options = [
        element for element in option_elements
        if option_text in element.text]
    if len(selected_options) != 1:
        raise Exception(
            str(
                'Could not find one single option with {} in text.\n'
                'found: {}').format(
                    option_text, [element.text for element in option_elements])
        )
    selected_options[0].click()
