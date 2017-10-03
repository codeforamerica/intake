import logging
from django.test import TestCase
from intake.tests.base_testcases import ALL_APPLICATION_FIXTURES
from django.contrib.auth.models import User
from user_accounts.models import Organization
from intake import models
import intake.services.transfers_service as TransferService
from project.tests.assertions import assertInLogsCount


class TestTransferApplication(TestCase):

    fixtures = ALL_APPLICATION_FIXTURES

    def test_creates_expected_objects(self):
        user = User.objects.filter(
            profile__organization__slug='a_pubdef').first()
        to_org = Organization.objects.get(slug='ebclc')
        application = models.Application.objects.filter(
            organization__slug='a_pubdef').first()
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            TransferService.transfer_application(
                user, application, to_org, 'because of subspace interference')
        new_application = models.Application.objects.filter(
            incoming_transfers__status_update__author=user).first()
        self.assertTrue(new_application.pk)
        self.assertEqual(new_application.incoming_transfers.count(), 1)
        transfer = new_application.incoming_transfers.first()
        self.assertEqual(
            transfer.status_update.status_type.slug, 'transferred')
        self.assertEqual(
            transfer.status_update.application.organization.county.slug,
            'alameda')
        self.assertEqual(transfer.reason, 'because of subspace interference')
        self.assertTrue(application.was_transferred_out)
        assertInLogsCount(logs, {'event_name=app_transferred': 1})

    def test_expected_number_of_queries(self):
        user = User.objects.filter(
            profile__organization__county__slug='alameda').first()
        to_org = Organization.objects.get(slug='ebclc')
        application = models.Application.objects.filter(
            organization__slug='a_pubdef').first()
        with self.assertNumQueries(19):
            TransferService.transfer_application(
                user, application, to_org, 'there was a temporal anomaly')
