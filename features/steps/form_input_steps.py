
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
