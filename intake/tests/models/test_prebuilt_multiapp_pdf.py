from django.test import TestCase
from user_accounts.tests.factories import FakeOrganizationFactory
from intake.tests.factories import FormSubmissionWithOrgsFactory
from intake import models


class TestPrebuiltMultiAppPDF(TestCase):

    def test_default_attributes(self):
        fake_org = FakeOrganizationFactory()
        subs = FormSubmissionWithOrgsFactory.create_batch(
            4, organizations=[fake_org], answers={})
        sub_ids = [sub.id for sub in subs]
        fake_apps = models.Application.objects.filter(
            form_submission__id__in=sub_ids)
        prebuilt = models.PrebuiltMultiAppPDF(
            organization=fake_org)
        prebuilt.save()
        prebuilt.applications.add(*fake_apps)
        self.assertFalse(prebuilt.pdf)
        self.assertEqual(prebuilt.organization, fake_org)
        self.assertEqual(set(prebuilt.applications.all()), set(fake_apps))
        self.assertIn('Unbuilt', str(prebuilt))
