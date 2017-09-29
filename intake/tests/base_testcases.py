import os
from unittest.mock import patch
from django.db.models import Count
from django.test import TestCase
from django.test import Client
from django.db import DEFAULT_DB_ALIAS, connections
from user_accounts.tests.base_testcases import AuthIntegrationTestCase
from intake import models
from intake.tests import mock
from .test_utils import AssertNumQueriesLessThanContext

from project.fixtures_index import (
    ESSENTIAL_DATA_FIXTURES,
    MOCK_USER_ACCOUNT_FIXTURES,
    MOCK_APPLICATION_FIXTURES,
    MOCK_BUNDLE_FIXTURES
)


DELUXE_TEST = os.environ.get('DELUXE_TEST', False)


ALL_APPLICATION_FIXTURES = (
    ESSENTIAL_DATA_FIXTURES +
    MOCK_USER_ACCOUNT_FIXTURES +
    MOCK_APPLICATION_FIXTURES
)

ALL_BUNDLES = MOCK_BUNDLE_FIXTURES


class IntakeDataTestCase(AuthIntegrationTestCase):

    display_field_checks = [
        'first_name',
        'last_name',
        'email',
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.have_a_fillable_pdf()
        org_subs = []
        cls.combo_submissions = list(
            models.FormSubmission.objects.annotate(
                apps_count=Count('applications')
            ).filter(apps_count__gt=1))
        for org in cls.orgs:
            subs = models.FormSubmission.objects.filter(
                applications__organization=org)
            subs = list(set(subs) - set(cls.combo_submissions))
            setattr(cls, org.slug + "_submissions", subs)
            org_subs += subs
            setattr(
                cls, org.slug + "_bundle",
                models.ApplicationBundle.objects.filter(
                    organization=org).first())
        cls.submissions = list(
            set(org_subs) | set(cls.combo_submissions)
        )

    @classmethod
    def have_a_fillable_pdf(cls):
        cls.fillable = mock.fillable_pdf(organization=cls.sf_pubdef)

    def assert_called_once_with_types(
            self, mock_obj, *arg_types, **kwarg_types):
        self.assertEqual(mock_obj.call_count, 1)
        arguments, keyword_arguments = mock_obj.call_args
        argument_classes = [getattr(
            arg, '__qualname__', arg.__class__.__qualname__
        ) for arg in arguments]
        self.assertListEqual(argument_classes, list(arg_types))
        keyword_argument_classes = {}
        for keyword, arg in keyword_arguments.items():
            keyword_argument_classes[keyword] = getattr(
                arg, '__qualname__', arg.__class__.__qualname__
            )
        self.assertDictEqual(keyword_argument_classes, dict(kwarg_types))


class ExternalNotificationsPatchTestCase(TestCase):

    def patch_json_serialization(self, mock_obj):
        """ensure that rendered notifications are json serializable"""
        mock_obj.render.return_value._asdict.return_value = {}

    def setUp(self):
        """patch outgoing externail notifications"""
        self.notifications_patcher = patch(
            'intake.service_objects.applicant_notifications.notifications')
        notifications = self.notifications_patcher.start()
        self.patch_json_serialization(notifications.email_followup)
        self.patch_json_serialization(notifications.sms_followup)
        self.patch_json_serialization(notifications.email_confirmation)
        self.patch_json_serialization(notifications.sms_confirmation)
        self.notifications = notifications

    def tearDown(self):
        self.notifications_patcher.stop()
        super().tearDown()


class APIViewTestCase(IntakeDataTestCase):

    client_class = Client

    fixtures = [
        'counties', 'organizations', 'groups', 'mock_profiles']


class DeluxeTransactionTestCase(TestCase):

    def assertNumQueriesLessThanEqual(self, num, func=None, *args, **kwargs):
        using = kwargs.pop("using", DEFAULT_DB_ALIAS)
        conn = connections[using]

        context = AssertNumQueriesLessThanContext(self, num, conn)
        if func is None:
            return context

        with context:
            func(*args, **kwargs)
