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

    def test_can_log_event(self):
        applicant = factories.ApplicantFactory()
        event_name = "im_being_tested"
        event = applicant.log_event(event_name)
        self.assertTrue(event.id)
        self.assertEqual(event.applicant, applicant)
        self.assertEqual(event.name, event_name)
        self.assertEqual(event.data, {})

        all_events = list(applicant.events.all())
        self.assertIn(event, all_events)

    def test_can_log_event_with_data(self):
        applicant = factories.ApplicantFactory()
        event_name = "im_being_tested"
        event_data = {"foo": "bar"}
        event = applicant.log_event(event_name, event_data)
        self.assertEqual(event.data, event_data)

    def test_permission_to_view_aggregate_stats(self):
        # given a user and a group
        # and the group has permission to view aggregate_stats
        user = User.objects.create(username='testuser')
        group = Group.objects.create(name="performance_monitors")
        permission = Permission.objects.get(
            name=permissions.CAN_SEE_APP_STATS.name)
        group.permissions.add(permission)
        user.groups.add(group)
        self.assertTrue(user.has_perm('intake.view_app_stats'))
