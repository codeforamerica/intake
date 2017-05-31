from django.test import TestCase
from user_accounts.tests.factories import OrganizationFactory
from intake.tests.factories import FormSubmissionWithOrgsFactory
from intake.models import PrebuiltMultiAppPDF


class TestPrebuiltMultiAppPDF(TestCase):

    def test_default_attributes(self):
        fake_org = OrganizationFactory()
        fake_apps = FormSubmissionWithOrgsFactory(
            organizations=[fake_org],
            answers={}).applications.all()
        prebuilt = PrebuiltMultiAppPDF(
            applications=fake_apps,
            organization=fake_org)
        import ipdb; ipdb.set_trace()
        # make a PDF with fake values
