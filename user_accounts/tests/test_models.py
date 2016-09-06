from django.test import TestCase
from intake.tests.test_views import IntakeDataTestCase


class TestUserProfile(IntakeDataTestCase):

    def test_user_should_see_pdf(self):
        self.assertTrue(self.sfpubdef_user.profile.should_see_pdf())
        self.assertTrue(self.cfa_user.profile.should_see_pdf())
        self.assertFalse(self.ccpubdef_user.profile.should_see_pdf())

    def test_should_have_access_to(self):
        for sub in self.submissions:
            self.assertTrue(self.cfa_user.profile.should_have_access_to(sub))
        for sub in self.sf_submissions:
            self.assertTrue(
                self.sfpubdef_user.profile.should_have_access_to(sub))
            self.assertFalse(
                self.ccpubdef_user.profile.should_have_access_to(sub))
        for sub in self.cc_submissions:
            self.assertFalse(
                self.sfpubdef_user.profile.should_have_access_to(sub))
            self.assertTrue(
                self.ccpubdef_user.profile.should_have_access_to(sub))


class TestOrganization(IntakeDataTestCase):

    def test_has_a_pdf(self):
        self.assertTrue(self.sfpubdef.has_a_pdf())
        self.assertFalse(self.ccpubdef.has_a_pdf())
