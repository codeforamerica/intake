from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission
from intake import models


class TestApplicant(TestCase):

    def test_can_create_with_nothing(self):
        applicant = models.Applicant()
        applicant.save()
        self.assertTrue(applicant.id)

    def test_can_log_event(self):
        applicant = models.Applicant()
        applicant.save()
        event_name = "im_being_tested"
        event = applicant.log_event(event_name)
        self.assertTrue(event.id)
        self.assertEqual(event.applicant, applicant)
        self.assertEqual(event.name, event_name)
        self.assertEqual(event.data, {})

        all_events = list(applicant.events.all())
        self.assertIn(event, all_events)

    def test_can_log_event_with_data(self):
        applicant = models.Applicant()
        applicant.save()
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
            name=models.applicant.Permissions.CAN_SEE_APP_STATS)
        group.permissions.add(permission)
        user.groups.add(group)
        self.assertTrue(user.has_perm('intake.view_app_stats'))
