from behave import given, when, then
from urllib.parse import urljoin, urlparse, urldefrag


@given('that "{url}" loads')
def load_page(context, url):
    context.browser.get(urljoin(context.test.live_server_url, url))


@then('it should load "{url}"')
def test_page_loads(context, url):
    browser_url = urlparse(context.browser.current_url)
    context.test.assertEquals(url, browser_url.path[1:])


@given('it loads css')
@then('it should load css')
def test_css_loads(context):
    selector = 'link[type="text/css"]'
    element = context.browser.find_element_by_css_selector(selector)
    css_url = urlparse(element.get_attribute('href'))
    domain_url = urlparse(context.test.live_server_url)
    context.test.assertEquals(css_url.hostname, domain_url.hostname)


"""
This is broken (don't konw how t select compress output)
@given('it loads js with name {name}')
@then('it should load js with name {name}')
def test_js_loads(context, name):
    selector = 'script[type="text/javascript"][name="{}"]'.format(name)
    element = context.browser.find_element_by_css_selector(selector)
    context.test.assertEquals(element.tag_name, 'script')
    js_url = urlparse(element.get_attribute('src'))
    domain_url = urlparse(context.test.live_server_url)
    context.test.assertEquals(js_url.hostname, domain_url.hostname)
"""


@then('it should have the "{element_id}" link and say "{text}"')
def find_with_id_and_assert_text(context, element_id, text):
    element = context.browser.find_element_by_id(element_id)
    context.test.assertEquals(element.text, text)


@then('"{element_id}" should deeplink to "{section}"')
def check_link_goes_to_section_but_stays_on_page(context, element_id, section):
    element = context.browser.find_element_by_id(element_id)
    start_url = urldefrag(context.browser.current_url)
    element.click()
    end_url = urldefrag(context.browser.current_url)
    context.test.assertEquals(start_url[0], end_url[0])
    context.test.assertEquals(end_url[1], section)


@then('"{element_id}" should link to "{url}"')
def check_link_goes_to_page(context, element_id, url):
    start_url = context.browser.current_url
    element = context.browser.find_element_by_id(element_id)
    element.click()
    end_url = context.browser.current_url
    context.test.assertNotEquals(start_url, end_url)
    context.test.assertEquals(
        urljoin(context.test.live_server_url, url),
        end_url,
    )


@when('"{checkbox_value}" is clicked on the "{checkbox_name}" radio button')
@when('the "{checkbox_name}" checkbox option "{checkbox_value}" is clicked')
def click_checkbox(context, checkbox_name, checkbox_value):
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


@then('"{element_class}" should say "{text}"')
def element_contains_text(context, element_class, text):
    element = context.browser.find_element_by_class_name(element_class)
    context.test.assertTrue(text in element.text)


@when('the "{input_name}" text input is set to "{value}"')
def type_in_textarea(context, input_name, value):
    selector = "input[name='%s'][type='text']" % (
        input_name,
    )
    text = context.browser.find_element_by_css_selector(selector)
    text.send_keys(value)
