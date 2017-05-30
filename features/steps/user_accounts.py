from urllib.parse import urljoin
from behave import given, when, then
from user_accounts.tests import factories
from user_accounts.models import Organization
from intake import groups
from django.conf import settings
from features.steps import forms


@given('an applicant support user')
def load_applicant_support_user(context):
    cfa = Organization.objects.get(slug='cfa')
    factories.profile_for_org_and_group_names(
        cfa, group_names=[groups.FOLLOWUP_STAFF, groups.APPLICATION_REVIEWERS],
        is_staff=True)


@when('I log in as "{email}"')
def login_as(context, email):
    context.browser.get(
        urljoin(context.test.live_server_url, '/accounts/login/'))
    forms.fill_text_input(context, 'login', email)
    forms.fill_text_input(context, 'password', settings.TEST_USER_PASSWORD)
    forms.click_submit_button(context)


@given('I log in as an applicant support user')
def login_as_applicant_support_user(context):
    login_as(context, "bgolder+demo+cfa_user@codeforamerica.org")
