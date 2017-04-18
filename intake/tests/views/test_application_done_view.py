from django.test import TestCase


class TestThanksView(TestCase):

    def test_redirects_to_home_if_no_applicant(self):
        pass

    def test_applicant_with_no_submission(self):
        pass

    def test_applicant_with_submission(self):
        pass

    def test_clears_session_data(self):
        pass

    def test_shows_organization_confirmation_messages(self):
        pass

    def test_shows_flash_messages(self):
        pass


class TestRAPSheetInstructionsView(TestCase):

    def test_works_without_applicant(self):
        pass

    def test_applicant_with_no_submission(self):
        pass

    def test_clears_session_data(self):
        pass

    def test_applicant_with_submission(self):
        pass

    def test_shows_flash_messages(self):
        pass