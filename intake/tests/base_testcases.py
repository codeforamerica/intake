import os
from unittest.mock import patch
from django.db.models import Count
from django.test import TestCase, Client
from django.test.utils import setup_test_environment
from user_accounts.tests.base_testcases import AuthIntegrationTestCase
from intake import models
from intake.tests import mock

DELUXE_TEST = os.environ.get('DELUXE_TEST', False)


ALL_APPLICATION_FIXTURES = [
    'counties',
    'organizations',
    'addresses',
    'mock_profiles',
    'mock_2_submissions_to_a_pubdef',
    'mock_2_submissions_to_ebclc',
    'mock_2_submissions_to_cc_pubdef',
    'mock_2_submissions_to_sf_pubdef',
    'mock_2_submissions_to_monterey_pubdef',
    'mock_2_submissions_to_solano_pubdef',
    'mock_2_submissions_to_san_diego_pubdef',
    'mock_2_submissions_to_san_joaquin_pubdef',
    'mock_2_submissions_to_santa_clara_pubdef',
    'mock_2_submissions_to_fresno_pubdef',
    'mock_2_submissions_to_santa_cruz_pubdef',
    'mock_2_submissions_to_sonoma_pubdef',
    'mock_2_submissions_to_tulare_pubdef',
    'mock_1_submission_to_multiple_orgs',
    'mock_application_events',
    'template_options'
]

ALL_BUNDLES = [
    'mock_1_bundle_to_a_pubdef',
    'mock_1_bundle_to_ebclc',
    'mock_1_bundle_to_sf_pubdef',
    'mock_1_bundle_to_cc_pubdef',
    'mock_1_bundle_to_monterey_pubdef',
    'mock_1_bundle_to_solano_pubdef',
    'mock_1_bundle_to_san_diego_pubdef',
    'mock_1_bundle_to_san_joaquin_pubdef',
    'mock_1_bundle_to_santa_clara_pubdef',
    'mock_1_bundle_to_sonoma_pubdef',
    'mock_1_bundle_to_fresno_pubdef',
    'mock_1_bundle_to_tulare_pubdef',
    'mock_1_bundle_to_santa_cruz_pubdef',
]


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

    def setUp(self):
        setup_test_environment()

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


class APIViewTestCase(IntakeDataTestCase):

    client_class = Client

    fixtures = [
        'counties', 'organizations', 'mock_profiles']
