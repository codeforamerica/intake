from behave import then
from easyaudit.models import CRUDEvent


@then('the latest CRUD event should not have a user')
def test_latest_crud_event_no_user(context):
    badevent = CRUDEvent.objects.latest('datetime')
    print(vars(badevent))
    context.test.assertIsNone(badevent.user)
