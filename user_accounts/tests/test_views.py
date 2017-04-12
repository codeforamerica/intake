from user_accounts.tests.base_testcases import AuthIntegrationTestCase
from django.core.urlresolvers import reverse
from project.fixtures_index import (
    ESSENTIAL_DATA_FIXTURES, MOCK_USER_ACCOUNT_FIXTURES
)


class TestUserProfileView(AuthIntegrationTestCase):
    fixtures = ESSENTIAL_DATA_FIXTURES + MOCK_USER_ACCOUNT_FIXTURES

    def test_can_see_org_in_auth_bar(self):
        user = self.be_sfpubdef_user()
        response = self.client.get(reverse('user_accounts-profile'))
        self.assertContains(response, user.profile.organization.name)
