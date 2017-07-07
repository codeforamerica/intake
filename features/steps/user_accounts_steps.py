from urllib.parse import urljoin
from behave import given, when
from user_accounts.tests import factories
from user_accounts.models import Organization
from intake import groups
from django.conf import settings
from features.steps import form_input_steps


@given('an applicant support user')
def load_applicant_support_user(context):
    org = Organization.objects.get(slug='cfa')
    factories.profile_for_org_and_group_names(
        org, group_names=[groups.FOLLOWUP_STAFF, groups.APPLICATION_REVIEWERS],
        is_staff=True)


@given('an org user')
@given('an org user at "{org_slug}"')
def load_org_user(context, org_slug='ebclc'):
    org = Organization.objects.get(slug=org_slug)
    factories.profile_for_org_and_group_names(
        org, group_names=[groups.APPLICATION_REVIEWERS])


@when('I log in as "{email}"')
def login_as(context, email):
    context.browser.get(
        urljoin(context.test.live_server_url, '/accounts/login/'))
    form_input_steps.fill_text_input(context, 'login', email)
    form_input_steps.fill_text_input(
        context, 'password', settings.TEST_USER_PASSWORD)
    form_input_steps.click_submit_button(context)
    context.execute_steps('''Then it should load "accounts/profile/"''')


@given('I log in as an applicant support user')
def login_as_applicant_support_user(context):
    login_as(context, "bgolder+demo+cfa_user@codeforamerica.org")


@given('I log in as an org user')
@given('I log in as an org user at "{org_slug}"')
@when('I log in as an org user at "{org_slug}"')
def login_as_org_user(context, org_slug='ebclc'):
    login_as(
        context, "bgolder+demo+{}_user@codeforamerica.org".format(org_slug))
