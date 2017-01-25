from user_accounts import exceptions
from intake.tests.base_testcases import IntakeDataTestCase


class TestUserProfile(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_cc_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs',
        'mock_1_bundle_to_cc_pubdef', 'template_options'
    ]

    def test_user_should_see_pdf(self):
        self.assertTrue(self.sf_pubdef_user.profile.should_see_pdf())
        self.assertTrue(self.cfa_user.profile.should_see_pdf())
        self.assertFalse(self.cc_pubdef_user.profile.should_see_pdf())

    def test_should_have_access_to_allows_staff_submission_access(self):
        for sub in self.submissions:
            self.assertTrue(self.cfa_user.profile.should_have_access_to(sub))

    def test_should_have_access_to_limits_submission_access_same_org(self):
        for sub in self.sf_pubdef_submissions:
            self.assertTrue(
                self.sf_pubdef_user.profile.should_have_access_to(sub))
            self.assertFalse(
                self.cc_pubdef_user.profile.should_have_access_to(sub))
        for sub in self.cc_pubdef_submissions:
            self.assertFalse(
                self.sf_pubdef_user.profile.should_have_access_to(sub))
            self.assertTrue(
                self.cc_pubdef_user.profile.should_have_access_to(sub))
        for sub in self.combo_submissions:
            self.assertTrue(
                self.cc_pubdef_user.profile.should_have_access_to(sub))
            self.assertTrue(
                self.sf_pubdef_user.profile.should_have_access_to(sub))

    def should_have_access_to_allows_staff_submission_access(self):
        bundle = self.cc_pubdef_bundle
        self.assertTrue(self.cfa_user.profile.should_have_access_to(bundle))
        self.assertTrue(
            self.cc_pubdef_user.profile.should_have_access_to(bundle))
        self.assertFalse(
            self.sf_pubdef_user.profile.should_have_access_to(bundle))

    def should_have_access_to_raises_error_for_other_objects(self):
        with self.assertRaises(exceptions.UndefinedResourceAccessError):
            self.cfa_user.profile.should_have_access_to({})
