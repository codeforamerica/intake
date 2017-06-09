from unittest.mock import patch
from django.test import TestCase
from django.db.utils import IntegrityError
from user_accounts.tests.factories import FakeOrganizationFactory
from intake.tests.factories import FormSubmissionWithOrgsFactory
from intake import models


class TestNewAppsPDF(TestCase):

    def test_default_attributes(self):
        fake_org = FakeOrganizationFactory()
        subs = FormSubmissionWithOrgsFactory.create_batch(
            4, organizations=[fake_org], answers={})
        sub_ids = [sub.id for sub in subs]
        fake_apps = models.Application.objects.filter(
            form_submission__id__in=sub_ids)
        prebuilt = models.NewAppsPDF(
            organization=fake_org)
        prebuilt.save()
        prebuilt.applications.add(*fake_apps)
        self.assertFalse(prebuilt.pdf)
        self.assertEqual(prebuilt.organization, fake_org)
        self.assertEqual(set(prebuilt.applications.all()), set(fake_apps))
        self.assertIn('Unbuilt', str(prebuilt))

    def test_two_for_same_org_raises_error(self):
        org = FakeOrganizationFactory()
        newapps_pdf = models.NewAppsPDF(organization=org)
        newapps_pdf.save()
        other_newapps_pdf = models.NewAppsPDF(organization=org)
        with self.assertRaises(IntegrityError):
            other_newapps_pdf.save()

    def test_set_pdf_to_bytes(self):
        newapps_pdf = models.NewAppsPDF(
            organization=FakeOrganizationFactory())
        bytes_ = b'zomg'
        newapps_pdf.set_bytes(bytes_)
        newapps_pdf.save()
        expected_filename = 'org-1_newapps'
        # pull from db to ensure cahnges persist
        fetched = models.NewAppsPDF.objects.first()
        self.assertIn(expected_filename, fetched.pdf.name)
        self.assertEqual(bytes_, fetched.pdf.read())
