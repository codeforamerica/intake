from urllib.parse import urljoin, urlparse
from unittest.mock import patch
from django.core.urlresolvers import reverse
from behave import given, then, when
from project.jinja2 import external_reverse
import intake.services.bundles as BundlesService


@given('it is a weekday')
def set_weekday(context):
    weekend_patcher = patch('intake.services.bundles.is_the_weekend')
    is_the_weekend = weekend_patcher.start()
    is_the_weekend.return_value = False
    context.test.patches["weekend_patcher"] = weekend_patcher


@then('org user at "{org_slug}" should receive the unreads email')
@patch('intake.notifications.SimpleFrontNotification.send')
def test_receives_unreads_email(context, send_front, org_slug):
    # initiate the email send (call bundle service)
    BundlesService.count_unreads_and_send_notifications_to_orgs()
    kall = send_front.call_args
    args, email = kall
    email['to'] = args[0]
    context.test.unreads_email = email
    expected_to = "bgolder+demo+{}_user@codeforamerica.org".format(org_slug)
    context.test.assertIn(expected_to, email['to'])


@then('I should see "{phrase}" in the email')
def test_phrase_in_email(context, phrase):
    # utility function: get_last_front_email (assert that this has an email)
    context.test.assertIn(phrase, context.test.unreads_email['body'])


@when('I click the unreads link in the email')
def follow_unreads_link_in_email(context):
    expected_unreads_link = external_reverse('intake-unread_email_redirect')
    context.test.assertIn(
        expected_unreads_link, context.test.unreads_email['body'])
    path = reverse('intake-unread_email_redirect')
    context.browser.get(urljoin(context.test.live_server_url, path))


@then('the app should send a slack notification about new CNL apps')
@patch('intake.notifications.slack_simple.send')
def test_sends_new_cnl_apps_slack(context, slack):
    BundlesService.count_unreads_and_send_notifications_to_orgs()
    call_args, keyword_args = slack.call_args
    slack_message = call_args[0]
    context.test.assertTrue(slack_message)
    context.test.new_cnl_app_slack = slack_message


@then('I should see "{phrase}" in the slack message about new CNL apps')
def test_phrase_in_email(context, phrase):
    context.test.assertIn(phrase, context.test.new_cnl_app_slack)


@when('I click on the link in the slack message about new CNL apps')
def follow_new_cnl_app_slack_link(context):
    expected_cnl_link = external_reverse('intake-app_cnl_index')
    context.test.assertIn(expected_cnl_link, context.test.new_cnl_app_slack)
    path = reverse('intake-app_cnl_index')
    context.browser.get(urljoin(context.test.live_server_url, path))
