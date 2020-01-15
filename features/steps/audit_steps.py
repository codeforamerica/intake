import json
from behave import when, then
from easyaudit.models import CRUDEvent
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from pprint import pprint
from urllib.parse import urljoin


def get_latest_crudevent_for_appmodel_and_event_type(content_type, event_type):
    # acceptable values are:
    #   "create", "update", "delete", "m2m_change", "m2m_change_rev"
    event_type_idx = getattr(CRUDEvent, event_type.upper())
    content_type_app, content_type_model = content_type.lower().split(".")
    event_model_content_type_id = ContentType.objects.filter(
        app_label=content_type_app,
        model=content_type_model).first().id
    return CRUDEvent.objects.filter(
        event_type=event_type_idx,
        content_type_id=event_model_content_type_id).latest('datetime')


@when('I go to the admin edit page for "{org_slug}" user')
def visit_org_user_admin_edit_page(context, org_slug):
    user = User.objects.filter(profile__organization__slug=org_slug).first()
    url = reverse('admin:auth_user_change', args=[user.id])
    context.browser.get(urljoin(context.test.live_server_url, url))


@then('the latest CRUD event should not have a user')
def test_latest_crud_event_no_user(context):
    badevent = CRUDEvent.objects.latest('datetime')
    print(vars(badevent))
    context.test.assertIsNone(badevent.user)


@then(str(
    'the latest "{content_type}" "{event_type}" event should have "{username}"'
    ' as the user'))
def test_crudevent_username(context, content_type, event_type, username):
    expected_event = get_latest_crudevent_for_appmodel_and_event_type(
        content_type, event_type)
    context.test.assertEqual(username, expected_event.user.username)


@then(str(
    'the latest "{content_type}" "{event_type}" event should have "{value}"'
    ' for "{key}"'))
def test_crudevent_has_matching_property(
        context, content_type, event_type, value, key):
    expected_event = get_latest_crudevent_for_appmodel_and_event_type(
        content_type, event_type)
    event_data = json.loads(expected_event.object_json_repr)[0]
    context.test.assertEqual(value, str(event_data["fields"][key]))


@then(str(
    'the latest "{content_type}" "{event_type}" event should have '
    '"{id_count}" ids in "{field_name}"'))
def test_crudevent_property_contains(
        context, content_type, event_type, id_count, field_name):
    expected_event = get_latest_crudevent_for_appmodel_and_event_type(
        content_type, event_type)
    event_data = json.loads(expected_event.object_json_repr)[0]
    context.test.assertEqual(
        int(id_count), len(event_data["fields"][field_name]))
