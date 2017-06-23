from behave import given, then, when
from urllib.parse import urljoin, urlparse


@when('I open "{url}"')
@given('that "{url}" loads')
def load_page(context, url):
    context.browser.get(urljoin(context.test.live_server_url, url))


@then('I should see a flash message that says "{text}"')
def test_flash_message_contains_text(context, text):
    element = context.browser.find_element_by_css_selector('.flash_messages')
    context.test.assertIn(text, element.text)


@when('I click the "{link_text}" link to "{url}"')
def follow_link_with_text(context, link_text, url):
    selector = 'a[href*="{url}"]'.format(url=url)
    element = context.browser.find_element_by_css_selector(selector)
    # it's a slight break in decorum to assert here, but seems like a useful
    # way to follow a link and be sure it says the right thing to the user
    context.test.assertIn(link_text, element.text)
    element.click()


@then('it should load "{url}"')
def test_page_loads(context, url):
    browser_url = urlparse(context.browser.current_url)
    expected_url = urlparse(urljoin(context.test.live_server_url, url))
    context.test.assertEquals(
        expected_url.path, browser_url.path)
    context.test.assertNotIn('Server Error', context.browser.page_source)


@then('it should have an iframe with "{iframe_src_url}"')
def test_iframe_exists_for_url(context, iframe_src_url):
    selector = 'iframe[src*="{}"]'.format(iframe_src_url)
    element = context.browser.find_element_by_css_selector(selector)
    context.test.assertTrue(element)


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


@then('it should have the element "{selector}" which says "{text}"')
def find_with_css_selector_and_assert_contains_text(context, selector, text):
    element = context.browser.find_element_by_css_selector(selector)
    context.test.assertIn(text, element.text)


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


@then('"{element_class}" should say "{text}"')
def element_contains_text(context, element_class, text):
    element = context.browser.find_element_by_class_name(element_class)
    context.test.assertTrue(text in element.text)


@then('the main heading should say "{text}"')
def test_main_heading_contains_text(context, text):
    main_heading = context.browser.find_element_by_css_selector('h1')
    context.test.assertIn(text, main_heading.text)
