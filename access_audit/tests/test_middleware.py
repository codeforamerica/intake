from project.tests.testcases import TestCase
from user_accounts.tests.factories import UserProfileFactory
from django.conf import settings
from easyaudit.middleware.easyaudit import (
    get_current_request, get_current_user)


class TestMiddleware(TestCase):
    """
    easyaudit does not properly clear requests after they're finished
    This means that users can be misattributed to subsequent actions.
    Our middleware forces the request to be cleared.
    """

    def test_request_is_cleared(self):
        # log in user
        user = UserProfileFactory().user
        self.client.login(
            username=user.username, password=settings.TEST_USER_PASSWORD)

        # do action
        self.client.get('/')
        # check if request is cleared
        self.assertIsNone(get_current_request())
        self.assertIsNone(get_current_user())
