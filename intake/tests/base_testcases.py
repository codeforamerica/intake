import os
from django.db.models import Count
from django.test.utils import setup_test_environment
from user_accounts.tests.base_testcases import AuthIntegrationTestCase
from intake import models
from intake.tests import mock

DELUXE_TEST = os.environ.get('DELUXE_TEST', False)


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
                orgs_count=Count('organizations')
            ).filter(orgs_count__gt=1))
        for org in cls.orgs:
            subs = models.FormSubmission.objects.filter(organizations=org)
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
