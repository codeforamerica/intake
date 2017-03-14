from django.test import TestCase
from django.contrib.auth.models import User
from user_accounts.models import Organization
from collections import OrderedDict
from intake import models
from intake.tests.base_testcases import ALL_APPLICATION_FIXTURES
import intake.services.applications_service as AppsService


class TestGetApplicationsIndexForOrgUser(TestCase):

    fixtures = ALL_APPLICATION_FIXTURES

    def test_results_for_org_who_cant_transfer(self):
        user = User.objects.filter(
            profile__organization__county__slug='solano').first()
        with self.assertNumQueries(7):
            results = AppsService.get_applications_index_for_org_user(user, 1)
        self.assertTrue(results.object_list)
        for thing in results:
            self.assertTrue(isinstance(thing, OrderedDict))

    def test_results_for_org_who_can_transfer(self):
        user = User.objects.filter(
            profile__organization__county__slug='alameda').first()
        with self.assertNumQueries(8):
            results = AppsService.get_applications_index_for_org_user(user, 1)
        self.assertTrue(results.object_list)
        for thing in results:
            self.assertTrue(isinstance(thing, OrderedDict))
            self.assertIn('incoming_transfers', thing)

    def test_results_for_org_who_has_outgoing_transfers(self):
        user = User.objects.filter(
            profile__organization__slug='a_pubdef').first()
        to_org = Organization.objects.get(slug='ebclc')
        application = models.Application.objects.filter(
            organization__county__slug='alameda').first()
        AppsService.transfer_application(
            user, application, to_org, 'because of subspace interference')
        with self.assertNumQueries(8):
            results = AppsService.get_applications_index_for_org_user(user, 1)
        self.assertTrue(
            any([
                app['was_transferred_out'] for app in results
            ]))

    def test_results_for_org_who_has_incoming_transfers(self):
        author = User.objects.filter(
            profile__organization__slug='a_pubdef').first()
        to_org = Organization.objects.get(slug='ebclc')
        applications = models.Application.objects.filter(
            organization__slug='a_pubdef')
        for application in applications:
            AppsService.transfer_application(
                author, application, to_org, 'temporal anomalies')
        user = User.objects.filter(
            profile__organization__slug='ebclc')[0]
        with self.assertNumQueries(13):
            results = AppsService.get_applications_index_for_org_user(user, 1)
        transferred_apps = [
            app for app in results if app['incoming_transfers']]
        self.assertTrue(transferred_apps)
        transfer = transferred_apps[0]['incoming_transfers'][0]
        self.assertEqual(
            transfer['organization_name'], author.profile.organization.name)
        self.assertEqual(
            transfer['author_name'], author.profile.name)
        self.assertEqual(
            transfer['reason'], 'temporal anomalies')


class TestTransferApplication(TestCase):

    fixtures = ALL_APPLICATION_FIXTURES

    def test_creates_expected_objects(self):
        user = User.objects.filter(
            profile__organization__slug='a_pubdef').first()
        to_org = Organization.objects.get(slug='ebclc')
        application = models.Application.objects.filter(
            organization__county__slug='alameda').first()
        AppsService.transfer_application(
            user, application, to_org, 'because of subspace interference')
        new_application = models.Application.objects.filter(
            incoming_transfers__status_update__author=user).first()
        self.assertTrue(new_application.pk)
        self.assertEqual(new_application.incoming_transfers.count(), 1)
        transfer = new_application.incoming_transfers.first()
        self.assertEqual(
            transfer.status_update.status_type.pk,
            models.status_type.TRANSFERRED)
        self.assertEqual(
            transfer.status_update.application.organization.county.slug,
            'alameda')
        self.assertEqual(transfer.reason, 'because of subspace interference')
        self.assertTrue(application.was_transferred_out)

    def test_expected_number_of_queries(self):
        user = User.objects.filter(
            profile__organization__county__slug='alameda').first()
        to_org = Organization.objects.get(slug='ebclc')
        application = models.Application.objects.filter(
            organization__county__slug='alameda').first()
        with self.assertNumQueries(4):
            AppsService.transfer_application(
                user, application, to_org, 'there was a temporal anomaly')
