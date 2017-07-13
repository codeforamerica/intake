from django.test import TestCase
from user_accounts.tests.factories import FakeOrganizationFactory
from intake.tests.factories import FormSubmissionWithOrgsFactory
from intake import models


class TestPrebuiltPDFBundle(TestCase):

    def test_default_attributes(self):
        fake_org = FakeOrganizationFactory()
        subs = FormSubmissionWithOrgsFactory.create_batch(
            4, organizations=[fake_org], answers={})
        sub_ids = [sub.id for sub in subs]
        fake_apps = models.Application.objects.filter(
            form_submission__id__in=sub_ids)
        prebuilt = models.PrebuiltPDFBundle(organization=fake_org)
        prebuilt.save()
        prebuilt.applications.add(*fake_apps)
        self.assertFalse(prebuilt.pdf)
        self.assertEqual(prebuilt.organization, fake_org)
        self.assertEqual(set(prebuilt.applications.all()), set(fake_apps))
        self.assertIn('Unbuilt', str(prebuilt))

    def test_set_pdf_to_bytes(self):
        prebuilt = models.PrebuiltPDFBundle(
            organization=FakeOrganizationFactory())
        bytes_ = b'zomg'
        prebuilt.set_bytes(bytes_)
        prebuilt.save()
        expected_filename = 'org-1_newapps'
        # pull from db to ensure changes persist
        fetched = models.PrebuiltPDFBundle.objects.first()
        self.assertIn(expected_filename, fetched.pdf.name)
        self.assertEqual(bytes_, fetched.pdf.read())

    def test_set_pdf_to_empty_bytes(self):
        prebuilt = models.PrebuiltPDFBundle(
            organization=FakeOrganizationFactory())
        bytes_ = b''
        prebuilt.set_bytes(bytes_)
        prebuilt.save()
        # pull from db to ensure cahnges persist
        fetched = models.PrebuiltPDFBundle.objects.first()
        self.assertFalse(fetched.pdf)
