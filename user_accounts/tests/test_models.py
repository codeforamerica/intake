from django.test import TestCase
from intake.tests.test_views import IntakeDataTestCase



class TestUserProfile(IntakeDataTestCase):

    def test_user_should_see_pdf(self):
        self.assertTrue(self.sfpubdef_user.profile.should_see_pdf())
        self.assertFalse(self.ccpubdef_user.profile.should_see_pdf())



class TestOrganization(IntakeDataTestCase):

    def test_has_a_pdf(self):
        self.assertTrue(self.sfpubdef.has_a_pdf())
        self.assertFalse(self.ccpubdef.has_a_pdf())