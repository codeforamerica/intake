import random
from unittest.mock import patch, Mock
from datetime import timedelta
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth.models import User
from user_accounts.models import Organization
from collections import OrderedDict
from intake import models
from intake.tests.base_testcases import (
    DeluxeTransactionTestCase, ALL_APPLICATION_FIXTURES)
from intake.tests import factories
import intake.services.applications_service as AppsService
import intake.services.transfers_service as TransferService
from user_accounts.tests.factories import \
    FakeOrganizationFactory, UserProfileFactory


class TestGetApplicationsIndexForOrgUser(TestCase):

    fixtures = ALL_APPLICATION_FIXTURES

    def test_all_results_for_org_who_cant_transfer(self):
        user = User.objects.filter(
            profile__organization__county__slug='solano').first()
        with self.assertNumQueries(6):
            results = AppsService.get_all_applications_for_org_user(user, 1)
        self.assertTrue(results.object_list)
        for thing in results:
            self.assertTrue(isinstance(thing, OrderedDict))

    def test_all_results_for_org_who_can_transfer(self):
        user = User.objects.filter(
            profile__organization__county__slug='alameda').first()
        with self.assertNumQueries(7):
            results = AppsService.get_all_applications_for_org_user(user, 1)
        self.assertTrue(results.object_list)
        for thing in results:
            self.assertTrue(isinstance(thing, OrderedDict))
            self.assertIn('incoming_transfers', thing)

    def test_all_results_for_org_who_has_outgoing_transfers(self):
        user = User.objects.filter(
            profile__organization__slug='a_pubdef').first()
        to_org = Organization.objects.get(slug='ebclc')
        application = models.Application.objects.filter(
            organization__county__slug='alameda').first()
        TransferService.transfer_application(
            user, application, to_org, 'food replicator malfunction')
        with self.assertNumQueries(5):
            results = AppsService.get_all_applications_for_org_user(user, 1)
        self.assertTrue(
            any([
                app['was_transferred_out'] for app in results
            ]))

    def test_all_results_for_org_who_has_incoming_transfers(self):
        author = User.objects.filter(
            profile__organization__slug='a_pubdef').first()
        to_org = Organization.objects.get(slug='ebclc')
        applications = models.Application.objects.filter(
            organization__slug='a_pubdef')
        for application in applications:
            TransferService.transfer_application(
                author, application, to_org, 'temporal anomalies')
        user = User.objects.filter(
            profile__organization__slug='ebclc')[0]
        with self.assertNumQueries(16):
            results = AppsService.get_all_applications_for_org_user(user, 1)
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

    def test_all_results_are_in_proper_order(self):
        user = User.objects.filter(
            profile__organization__slug='cc_pubdef').first()
        results = AppsService.get_all_applications_for_org_user(user, 1)
        future = timezone.now() + timedelta(days=10000)
        for item in results:
            date = item['form_submission']['local_date_received']
            self.assertTrue(date <= future)
            future = date

    def test_unread_results_only_include_unreads(self):
        user = User.objects.filter(
            profile__organization__slug='a_pubdef').first()
        results = AppsService.get_unread_applications_for_org_user(user, 1)
        self.assertFalse(
            any([
                app['has_been_opened'] for app in results
            ]))

    def test_needs_updates_results_only_include_apps_needing_update(self):
        user = User.objects.filter(
            profile__organization__slug='a_pubdef').first()
        results = AppsService.get_applications_needing_updates_for_org_user(
            user, 1)
        self.assertFalse(
            any([
                app['status_updates'] for app in results
            ]))

    def all_results_include_unread_apps(self):
        user = User.objects.filter(
            profile__organization__slug='a_pubdef').first()
        results = AppsService.get_all_applications_for_org_user(user, 1)
        self.assertTrue(
            any([
                app['has_been_opened'] for app in results
            ]))


class TestGetSerializedApplicationHistoryEvents(DeluxeTransactionTestCase):

    fixtures = ALL_APPLICATION_FIXTURES

    def test_number_of_queries_for_no_transfers(self):
        application = models.Application.objects.filter(
            organization__slug='a_pubdef').first()
        author = User.objects.filter(
            profile__organization__slug='a_pubdef').first()
        # make more status updates
        new_updates_count = random.randint(1, 7)
        for i in range(new_updates_count):
            factories.StatusUpdateFactory.create(
                application=application, author=author)
        with self.assertNumQueriesLessThanEqual(9):
            AppsService.get_serialized_application_history_events(
                application, author)

    def test_number_of_queries_if_transferred_in(self):
        author = User.objects.filter(
            profile__organization__slug='a_pubdef').first()
        application = models.Application.objects.filter(
            organization__slug='a_pubdef').first()
        to_org = Organization.objects.get(slug='ebclc')
        receiving_user = User.objects.filter(
            profile__organization__slug='ebclc').first()
        transfer, *other = TransferService.transfer_application(
            author, application, to_org, 'holodeck malfunction')
        app = transfer.new_application
        new_updates_count = random.randint(1, 7)
        for i in range(new_updates_count):
            factories.StatusUpdateFactory.create(
                application=app, author=receiving_user)
        with self.assertNumQueriesLessThanEqual(14):
            AppsService.get_serialized_application_history_events(
                application, receiving_user)


class TestHandleAppsOpened(TestCase):
    def test_mark_only_users_app_opened(self):
        fake_org_1 = FakeOrganizationFactory()
        fake_org_2 = FakeOrganizationFactory()
        sub = factories.FormSubmissionWithOrgsFactory(
            organizations=[fake_org_1, fake_org_2], answers={})
        org_1_user = UserProfileFactory(organization=fake_org_1).user
        AppsService.handle_apps_opened(
            Mock(**{'request.user': org_1_user}),
            sub.applications.all(), False)
        org_1_apps = sub.applications.filter(organization=fake_org_1)
        org_2_apps = sub.applications.filter(organization=fake_org_2)
        self.assertTrue(all([app.has_been_opened for app in org_1_apps]))
        self.assertFalse(any([app.has_been_opened for app in org_2_apps]))

    @patch('intake.tasks.remove_application_pdfs')
    def test_calls_remove_pdf_task_when_opened(self, remove_application_pdfs):
        profile = UserProfileFactory()
        sub = factories.FormSubmissionWithOrgsFactory(
            organizations=[profile.organization], answers={})
        AppsService.handle_apps_opened(
            Mock(**{'request.user': profile.user}),
            sub.applications.all(), False)
        remove_application_pdfs.delay.assert_called_with(
            sub.applications.first().id)
