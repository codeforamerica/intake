from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission
from django.db.utils import IntegrityError
from intake import models, permissions
from intake.tests import factories


class TestApplicant(TestCase):

    def test_cant_create_with_nothing(self):
        applicant = models.Applicant()
        with self.assertRaises(IntegrityError):
            applicant.save()

    def test_can_create_with_visitor_id(self):
        visitor = factories.VisitorFactory()
        applicant = models.Applicant(visitor_id=visitor.id)
        applicant.save()
        self.assertTrue(applicant.id)

    def test_getuuid_returns_same_uuid_as_corresponding_visitor(self):
        visitor = factories.VisitorFactory()
        applicant = models.Applicant(visitor_id=visitor.id)
        applicant.save()
        self.assertEqual(applicant.get_uuid(), visitor.get_uuid())

    def test_there_can_be_only_one_applicant_per_visitor(self):
        # aka highlander test
        applicant = factories.ApplicantFactory()
        visitor = applicant.visitor
        second_applicant = models.Applicant(visitor_id=visitor.id)
        with self.assertRaises(IntegrityError):
            second_applicant.save()
        self.assertEqual(visitor.applicant, applicant)
