from behave import given, when, then
from urllib.parse import urljoin, urlparse, urldefrag


@then('it should load "{url}"')
@given('that "{url}" loads')
def load_page(context, url):
    context.browser.get(urljoin(context.test.live_server_url, url))


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


@when('the "{checkbox_name}" checkbox option "{checkbox_value}" is clicked')
def click_checkbox(context, checkbox_name, checkbox_value):
    selector = "input[name='%s'][value='%s'][type='checkbox']" % (
        checkbox_name,
        checkbox_value,
    )
    checkbox = context.browser.find_element_by_css_selector(selector)
    checkbox.click()


@when('submit button in form "{form_class}" is clicked')
def click_checkbox(context, form_class):
    selector = "form.%s button[type='submit']" % (
        form_class,
    )
    checkbox = context.browser.find_element_by_css_selector(selector)
    checkbox.click()

@then('"{element_class}" should say "{text}"')
def element_contains_text(context, element_class, text):
    element = context.browser.find_element_by_class(element_class)
    context.test.assertTrue(text in element.text)
