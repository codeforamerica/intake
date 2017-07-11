from behave import given, then, when
from unittest.mock import patch
import intake.services.bundles as BundlesService


@given('it is a weekday')
def set_weekday(context):
    weekend_patcher = patch('intake.utils.is_the_weekend')
    weekend_patcher.return_value = False
    weekend_patcher.start()
    context.test.patches["weekend_patcher"] = weekend_patcher


@given('Front is patched')
def patch_front_notifications(context):
    front_patcher = patch(
        'intake.notifications.SimpleFrontNotification.send')
    front_patcher.start()
    context.test.patches["front"] = front_patcher


@then('I should receive the unreads email')
def test_receives_unreads_email(context):
    print(context.test.patches)
    front = context.test.patches["front"]
    front.start()
    # initiate the email send (call bundle service)
    BundlesService.count_unreads_and_send_notifications_to_orgs()
    # pull email from mock calls on patch

    print(front.mock_calls)
    front.assert_called_once()



@then('I should see "{phrase}" in the email')
def test_phrase_in_email(context, phrase):
    # utility function: get_last_front_email (assert that this has an email)
    pass


@when('I click the unreads link in the email')
def follow_unreads_link_in_email(context):
    pass
