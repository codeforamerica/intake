from unittest import skipUnless
from unittest.mock import patch
from random import randint

from django.core.urlresolvers import reverse
from django.utils import html as html_utils
from django.core.files.uploadedfile import SimpleUploadedFile

from intake import models, constants
from user_accounts import models as auth_models
from intake.tests.base_testcases import IntakeDataTestCase, DELUXE_TEST
from intake.tests.mock import FormSubmissionFactory
from project.jinja2 import url_with_ids

import intake.services.bundles as BundlesService


class TestApplicationDetail(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs', 'template_options'
    ]

    def get_detail(self, submission):
        url = reverse(
            'intake-app_detail', kwargs=dict(submission_id=submission.id))
        result = self.client.get(url)
        return result

    def assertHasDisplayData(self, response, submission):
        for field, value in submission.answers.items():
            if field in self.display_field_checks:
                escaped_value = html_utils.conditional_escape(value)
                self.assertContains(response, escaped_value)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_logged_in_user_can_get_submission_display(self, slack):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_detail(submission)
        self.assertEqual(response.context_data['form'].submission, submission)
        self.assertHasDisplayData(response, submission)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_staff_user_can_get_submission_display(self, slack):
        self.be_cfa_user()
        submission = self.a_pubdef_submissions[0]
        result = self.get_detail(submission)
        self.assertEqual(result.context_data['form'].submission, submission)
        self.assertHasDisplayData(result, submission)

    @patch('intake.models.FillablePDF')
    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_with_pdf_redirected_to_pdf(self, slack, FillablePDF):
        self.be_sfpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        result = self.get_detail(submission)
        self.assertRedirects(
            result,
            reverse(
                'intake-filled_pdf', kwargs=dict(submission_id=submission.id)),
            fetch_redirect_response=False)
        slack.assert_not_called()  # notification should be handled by pdf view
        FillablePDF.assert_not_called()

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_cant_see_app_detail_for_other_county(self, slack):
        self.be_ccpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        response = self.get_detail(submission)
        self.assertRedirects(response, reverse('intake-app_index'))
        slack.assert_not_called()

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_can_see_app_detail_for_multi_county(self, slack):
        self.be_apubdef_user()
        submission = self.combo_submissions[0]
        response = self.get_detail(submission)
        self.assertHasDisplayData(response, submission)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_agency_user_can_see_transfer_action_link(self, slack):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_detail(submission)
        transfer_action_url = html_utils.conditional_escape(
            submission.get_transfer_action(response.wsgi_request)['url'])
        self.assertContains(response, transfer_action_url)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_agency_user_can_see_case_printout_link(self, slack):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_detail(submission)
        printout_url = html_utils.conditional_escape(
            submission.get_case_printout_url())
        self.assertContains(response, printout_url)


class TestApplicationBundle(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs',
        'mock_1_bundle_to_sf_pubdef',
        'mock_1_bundle_to_a_pubdef', 'template_options'
    ]

    def get_submissions(self, group):
        ids = [s.id for s in group]
        url = url_with_ids('intake-app_bundle', ids)
        return self.client.get(url)

    def assertHasDisplayData(self, response, submissions):
        for submission in submissions:
            for field, value in submission.answers.items():
                if field in self.display_field_checks:
                    escaped_value = html_utils.conditional_escape(value)
                    self.assertContains(response, escaped_value)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_can_get_app_bundle_without_pdf(self, slack):
        self.be_apubdef_user()
        response = self.get_submissions(self.a_pubdef_submissions)
        self.assertNotContains(response, 'iframe class="pdf_inset"')
        self.assertHasDisplayData(response, self.a_pubdef_submissions)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_staff_user_can_get_app_bundle_with_pdf(self, slack):
        self.be_cfa_user()
        response = self.get_submissions(self.combo_submissions)
        self.assertContains(response, 'iframe class="pdf_inset"')
        self.assertHasDisplayData(response, self.combo_submissions)

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_can_get_bundle_with_pdf(self, slack):
        self.be_sfpubdef_user()
        response = self.get_submissions(self.sf_pubdef_submissions)
        self.assertContains(response, 'iframe class="pdf_inset"')

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_cant_see_app_bundle_for_other_county(self, slack):
        self.be_sfpubdef_user()
        response = self.get_submissions(self.a_pubdef_submissions)
        self.assertEqual(response.status_code, 404)
        slack.assert_not_called()

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_user_can_see_app_bundle_for_multi_county(self, slack):
        self.be_apubdef_user()
        response = self.get_submissions(self.combo_submissions)
        self.assertNotContains(response, 'iframe class="pdf_inset"')
        self.assertHasDisplayData(response, self.combo_submissions)


class TestApplicationIndex(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs',
        'mock_1_bundle_to_sf_pubdef',
        'mock_1_bundle_to_a_pubdef', 'template_options'
    ]

    def assertContainsSubmissions(self, response, submissions):
        for submission in submissions:
            detail_url_link = reverse('intake-app_detail',
                                      kwargs=dict(submission_id=submission.id))
            self.assertContains(response, detail_url_link)

    def assertNotContainsSubmissions(self, response, submissions):
        for submission in submissions:
            detail_url_link = reverse('intake-app_detail',
                                      kwargs=dict(submission_id=submission.id))
            self.assertNotContains(response, detail_url_link)

    def test_that_number_of_queries_are_reasonable(self):
        self.be_cfa_user()
        random_new_subs_count = randint(5, 20)
        for i in range(random_new_subs_count):
            FormSubmissionFactory.create()
        with self.assertNumQueries(17):
            self.client.get(reverse('intake-app_index'))

    def test_that_org_user_can_only_see_apps_to_own_org(self):
        self.be_apubdef_user()
        response = self.client.get(reverse('intake-app_index'))
        self.assertContainsSubmissions(response, self.a_pubdef_submissions)
        self.assertContainsSubmissions(response, self.combo_submissions)
        self.assertNotContainsSubmissions(response, self.sf_pubdef_submissions)

    def test_that_cfa_user_can_see_apps_to_all_orgs(self):
        self.be_cfa_user()
        response = self.client.get(reverse('intake-app_index'))
        self.assertContainsSubmissions(response, self.submissions)

    def test_org_user_sees_name_of_org_in_index(self):
        user = self.be_ccpubdef_user()
        response = self.client.get(reverse('intake-app_index'))
        self.assertContains(response, user.profile.organization.name)

    def test_followup_staff_sees_notes(self):
        self.be_cfa_user()
        response = self.client.get(reverse('intake-app_index'))
        self.assertContains(response, "Save note")

    def test_pdf_users_see_pdf_link(self):
        self.be_sfpubdef_user()
        # look for the pdf link of each app
        response = self.client.get(reverse('intake-app_index'))
        self.assertEqual(response.context_data['show_pdf'], True)
        for sub in self.sf_pubdef_submissions:
            pdf_url = reverse('intake-filled_pdf', kwargs=dict(
                submission_id=sub.id))
            self.assertContains(response, pdf_url)

    def test_non_pdf_users_dont_see_pdf_link(self):
        self.be_apubdef_user()
        # look for the pdf link of each app
        response = self.client.get(reverse('intake-app_index'))
        self.assertEqual(response.context_data['show_pdf'], False)
        for sub in self.combo_submissions:
            pdf_url = reverse('intake-filled_pdf', kwargs=dict(
                submission_id=sub.id))
            self.assertNotContains(response, pdf_url)

    def test_user_can_see_case_detail_printout_links(self):
        self.be_apubdef_user()
        response = self.client.get(reverse('intake-app_index'))
        for sub in self.a_pubdef_submissions:
            printout_url = html_utils.conditional_escape(
                sub.get_case_printout_url())
            self.assertContains(response, printout_url)

    def test_user_can_see_update_status_links(self):
        self.be_apubdef_user()
        response = self.client.get(reverse('intake-app_index'))
        for sub in self.a_pubdef_submissions:
            update_status_url = html_utils.conditional_escape(
                sub.get_case_update_status_url())
            self.assertContains(response, update_status_url)

    def test_that_nonstaff_cfa_user_cant_see_apps(self):
        self.be_monitor_user()
        response = self.client.get(reverse('intake-app_index'))
        self.assertEqual(response.status_code, 302)

    def test_org_user_can_see_latest_status_of_app(self):
        user = self.be_apubdef_user()
        response = self.client.get(reverse('intake-app_index'))
        for sub in self.a_pubdef_submissions:
            status = sub.applications.filter(
                organization=user.profile.organization).first(
            ).status_updates.latest('updated').status_type.display_name
            self.assertContains(
                response, html_utils.conditional_escape(status))


class TestApplicationBundleDetail(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_sf_pubdef', 'template_options',
        'mock_1_submission_to_multiple_orgs',
        'mock_1_bundle_to_a_pubdef'
    ]

    @patch(
        'intake.views.admin_views.notifications.slack_submissions_viewed.send')
    def test_returns_200_on_existing_bundle_id(self, slack):
        """`ApplicationBundleDetailView` return `OK` for existing bundle

        create an `ApplicationBundle`,
        try to access `ApplicationBundleDetailView` using `id`
        assert that 200 OK is returned
        """
        self.be_apubdef_user()
        result = self.client.get(reverse(
            'intake-app_bundle_detail',
            kwargs=dict(bundle_id=self.a_pubdef_bundle.id)))
        self.assertEqual(result.status_code, 200)

    @patch(
        'intake.views.admin_views.notifications.slack_submissions_viewed.send')
    def test_staff_user_gets_200(self, slack):
        self.be_cfa_user()
        result = self.client.get(reverse(
            'intake-app_bundle_detail',
            kwargs=dict(bundle_id=self.a_pubdef_bundle.id)))
        self.assertEqual(result.status_code, 200)

    def test_returns_404_on_nonexisting_bundle_id(self):
        """ApplicationBundleDetailView return 404 if not found

        with no existing `ApplicationBundle`
        try to access `ApplicationBundleDetailView` using a made up `id`
        assert that 404 is returned
        """
        self.be_ccpubdef_user()
        result = self.client.get(reverse(
            'intake-app_bundle_detail',
            kwargs=dict(bundle_id=20909872435)))
        self.assertEqual(result.status_code, 404)

    def test_user_from_wrong_org_is_redirected_to_app_index(self):
        """ApplicationBundleDetailView redirects unpermitted users

        with existing `ApplicationBundle`
        try to access `ApplicationBundleDetailView` as a user from another org
        assert that redirects to `ApplicationIdex`
        """
        self.be_sfpubdef_user()
        result = self.client.get(reverse(
            'intake-app_bundle_detail',
            kwargs=dict(bundle_id=self.a_pubdef_bundle.id)))
        self.assertRedirects(
            result, reverse('intake-app_index'), fetch_redirect_response=False)

    @patch(
        'intake.views.admin_views.notifications.slack_submissions_viewed.send')
    def test_has_pdf_bundle_url_if_needed(self, slack):
        """ApplicationBundleDetailView return pdf url if needed

        create an `ApplicationBundle` that needs a pdf
        try to access `ApplicationBundleDetailView` using `id`
        assert that the url for `FilledPDFBundle` is in the template.
        """
        self.be_sfpubdef_user()
        mock_pdf = SimpleUploadedFile(
            'a.pdf', b"things", content_type="application/pdf")
        bundle = BundlesService.create_bundle_from_submissions(
            organization=self.sf_pubdef,
            submissions=self.sf_pubdef_submissions,
            bundled_pdf=mock_pdf
        )
        url = bundle.get_pdf_bundle_url()
        result = self.client.get(reverse(
            'intake-app_bundle_detail',
            kwargs=dict(bundle_id=bundle.id)))
        self.assertContains(result, url)

    @patch(
        'intake.notifications.slack_submissions_viewed.send')
    def test_agency_user_can_see_transfer_action_links(self, slack):
        self.be_apubdef_user()
        response = self.client.get(
            self.a_pubdef_bundle.get_absolute_url())
        for sub in self.a_pubdef_submissions:
            transfer_action_url = html_utils.conditional_escape(
                sub.get_transfer_action(response.wsgi_request)['url'])
            self.assertContains(response, transfer_action_url)

    @patch(
        'intake.notifications.slack_submissions_viewed.send')
    def test_user_can_see_app_bundle_printout_link(self, slack):
        self.be_apubdef_user()
        response = self.client.get(self.a_pubdef_bundle.get_absolute_url())
        printout_url = html_utils.conditional_escape(
            self.a_pubdef_bundle.get_printout_url())
        self.assertContains(response, printout_url)


@skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
class TestApplicationBundleDetailPDFView(IntakeDataTestCase):
    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_sf_pubdef', 'template_options',
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # patch slack_simple
        patcher = patch('intake.notifications')
        patcher.start()
        cls.bundle = BundlesService.create_bundle_from_submissions(
            organization=cls.sf_pubdef, submissions=cls.sf_pubdef_submissions)
        patcher.stop()

    def test_staff_user_gets_200(self):
        self.be_cfa_user()
        response = self.client.get(self.bundle.get_pdf_bundle_url())
        self.assertEqual(response.status_code, 200)

    def test_user_from_same_org_gets_200(self):
        self.be_sfpubdef_user()
        response = self.client.get(self.bundle.get_pdf_bundle_url())
        self.assertEqual(response.status_code, 200)

    def test_user_from_other_org_gets_404(self):
        self.be_ccpubdef_user()
        response = self.client.get(self.bundle.get_pdf_bundle_url())
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_pdf_returns_404(self):
        self.be_cfa_user()
        bundle = BundlesService.create_bundle_from_submissions(
            organization=self.sf_pubdef,
            submissions=self.sf_pubdef_submissions,
            skip_pdf=True)
        response = self.client.get(bundle.get_pdf_bundle_url())
        self.assertEqual(response.status_code, 404)


class TestReferToAnotherOrgView(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_1_bundle_to_a_pubdef', 'template_options']

    def setUp(self):
        super().setUp()
        self.mock_sub_id = self.a_pubdef_submissions[0].id
        self.mock_bundle_id = self.a_pubdef_bundle.id

    def url(self, org_id, sub_id=None, next=None):
        sub_id = sub_id or self.mock_sub_id
        base = reverse(
            'intake-mark_transferred_to_other_org')
        base += "?ids={sub_id}&to_organization_id={org_id}".format(
            sub_id=sub_id, org_id=org_id)
        if next:
            base += "&next={}".format(next)
        return base

    @patch('intake.views.admin_views.notifications'
           '.slack_submission_transferred.send')
    def test_anon_is_rejected(self, slack_action):
        self.be_anonymous()
        response = self.client.get(self.url(
            1))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_accounts-login'), response.url)
        slack_action.assert_not_called()

    @patch(
        'intake.views.admin_views.notifications.slack_submission_transferred')
    def test_org_user_with_no_next_is_redirected_to_app_index(self,
                                                              slack_action):
        self.be_apubdef_user()
        sub = models.FormSubmission.objects.get(pk=self.mock_sub_id)
        ebclc = auth_models.Organization.objects.get(
            slug=constants.Organizations.EBCLC)
        response = self.client.get(self.url(
            org_id=ebclc.id))
        self.assertRedirects(
            response, reverse('intake-app_index'),
            fetch_redirect_response=False)
        sub_url = sub.get_absolute_url()
        index = self.client.get(response.url)
        self.assertNotContains(index, sub_url)
        self.assertContains(index, "You successfully transferred")
        self.assertEqual(len(list(slack_action.mock_calls)), 1)

    @patch(
        'intake.views.admin_views.notifications.slack_submissions_viewed.send')
    @patch(
        'intake.views.admin_views.notifications.slack_submission_transferred')
    def test_org_user_with_next_goes_back_to_next(self,
                                                  slack_action,
                                                  slack_viewed):
        self.be_apubdef_user()
        sub = models.FormSubmission.objects.get(pk=self.mock_sub_id)
        bundle = models.ApplicationBundle.objects.get(pk=self.mock_bundle_id)
        ebclc = auth_models.Organization.objects.get(
            slug=constants.Organizations.EBCLC)
        response = self.client.get(self.url(
            org_id=ebclc.id, next=bundle.get_absolute_url()))
        self.assertRedirects(
            response, bundle.get_absolute_url(),
            fetch_redirect_response=False)
        bundle_page = self.client.get(response.url)
        self.assertNotContains(
            bundle_page,
            "formsubmission-{}".format(sub.id),
        )
        self.assertContains(bundle_page, "You successfully transferred")
        self.assertEqual(len(list(slack_action.mock_calls)), 1)
        self.assertEqual(len(list(slack_viewed.mock_calls)), 1)
