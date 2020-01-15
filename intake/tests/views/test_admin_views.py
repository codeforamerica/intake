import logging
from unittest import skipUnless
from unittest.mock import patch
from random import randint

from django.conf import settings
from django.urls import reverse
from django.utils import html as html_utils
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from bs4 import BeautifulSoup

from intake import models
from intake.tests.base_testcases import IntakeDataTestCase, DELUXE_TEST
from intake.tests.factories import FormSubmissionFactory, make_apps_for
from user_accounts.tests.factories import followup_user, app_reviewer
from project.services.query_params import get_url_for_ids
import intake.services.bundles as BundlesService
from project.tests.assertions import assertInLogsCount


class TestApplicationDetail(IntakeDataTestCase):

    fixtures = [
        'counties', 'groups',
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

    def test_logged_in_user_can_get_submission_display(self):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            response = self.get_detail(submission)
        self.assertEqual(response.context_data['form'].submission, submission)
        self.assertHasDisplayData(response, submission)
        assertInLogsCount(logs, {'event_name=app_opened': 1})

    def test_staff_user_can_get_submission_display(self):
        self.be_cfa_user()
        submission = self.a_pubdef_submissions[0]
        result = self.get_detail(submission)
        self.assertEqual(result.context_data['form'].submission, submission)
        self.assertHasDisplayData(result, submission)

    def test_user_cant_see_app_detail_for_other_county(self):
        self.be_ccpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        response = self.get_detail(submission)
        self.assertRedirects(response, reverse('user_accounts-profile'))

    def test_user_can_see_app_detail_for_multi_county(self):
        self.be_apubdef_user()
        submission = self.combo_submissions[0]
        response = self.get_detail(submission)
        self.assertHasDisplayData(response, submission)

    def test_multicounty_app_marked_as_viewed_by_users_org_only(self):
        user = self.be_apubdef_user()
        submission = self.combo_submissions[0]
        self.get_detail(submission)
        application = submission.applications.filter(
            organization=user.profile.organization).first()
        self.assertTrue(application.has_been_opened)
        other_apps = submission.applications.exclude(
            organization=user.profile.organization)
        self.assertFalse(all([app.has_been_opened for app in other_apps]))

    def test_agency_user_can_see_transfer_action_link(self):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_detail(submission)
        transfer_action_url = html_utils.conditional_escape(
            submission.get_transfer_action(response.wsgi_request)['url'])
        self.assertContains(response, transfer_action_url)

    def test_agency_user_can_see_case_printout_link(self):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_detail(submission)
        printout_url = html_utils.conditional_escape(
            submission.get_case_printout_url())
        self.assertContains(response, printout_url)

    def test_marks_apps_as_opened(self):
        user = self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        self.get_detail(submission)
        application = submission.applications.filter(
            organization=user.profile.organization).first()
        self.assertTrue(application.has_been_opened)


class TestApplicationBundle(IntakeDataTestCase):

    fixtures = [
        'counties', 'groups',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs',
        'mock_1_bundle_to_sf_pubdef',
        'mock_1_bundle_to_a_pubdef', 'template_options'
    ]

    def get_submissions(self, group):
        ids = [s.id for s in group]
        url = get_url_for_ids('intake-app_bundle', ids)
        return self.client.get(url)

    def assertHasDisplayData(self, response, submissions):
        for submission in submissions:
            for field, value in submission.answers.items():
                if field in self.display_field_checks:
                    escaped_value = html_utils.conditional_escape(value)
                    self.assertContains(response, escaped_value)

    def test_user_can_get_app_bundle_without_pdf(self):
        self.be_apubdef_user()
        response = self.get_submissions(self.a_pubdef_submissions)
        self.assertNotContains(response, 'iframe class="pdf_inset"')
        self.assertHasDisplayData(response, self.a_pubdef_submissions)

    def test_staff_user_can_get_app_bundle_with_pdf(self):
        self.be_cfa_user()
        response = self.get_submissions(self.combo_submissions)
        self.assertContains(response, 'iframe class="pdf_inset"')
        self.assertHasDisplayData(response, self.combo_submissions)

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
    def test_user_can_get_bundle_with_pdf(self):
        self.be_sfpubdef_user()
        response = self.get_submissions(self.sf_pubdef_submissions)
        self.assertContains(response, 'iframe class="pdf_inset"')

    def test_bundle_with_pdf_marks_apps_as_opened(self):
        user = self.be_sfpubdef_user()
        self.get_submissions(self.sf_pubdef_submissions)
        apps = models.Application.objects.filter(
                organization=user.profile.organization,
                form_submission__id__in=[
                    sub.id for sub in self.sf_pubdef_submissions])
        self.assertTrue(all([app.has_been_opened for app in apps]))

    def test_user_cant_see_app_bundle_for_other_county(self):
        self.be_sfpubdef_user()
        response = self.get_submissions(self.a_pubdef_submissions)
        self.assertEqual(response.status_code, 404)

    def test_user_can_see_app_bundle_for_multi_county(self):
        self.be_apubdef_user()
        response = self.get_submissions(self.combo_submissions)
        self.assertNotContains(response, 'iframe class="pdf_inset"')
        self.assertHasDisplayData(response, self.combo_submissions)

    def test_marks_apps_as_opened(self):
        user = self.be_apubdef_user()
        self.get_submissions(self.a_pubdef_submissions)
        apps = models.Application.objects.filter(
            organization=user.profile.organization,
            form_submission__id__in=[
                sub.id for sub in self.a_pubdef_submissions])
        self.assertTrue(all([app.has_been_opened for app in apps]))


class TestApplicationIndex(IntakeDataTestCase):

    fixtures = [
        'counties', 'groups',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs',
        'mock_1_bundle_to_sf_pubdef',
        'mock_1_bundle_to_a_pubdef', 'template_options',
        'mock_2_transfers'
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
        with self.assertNumQueries(22):
            self.client.get(reverse('intake-app_all_index'))

    def test_that_org_user_can_only_see_apps_to_own_org(self):
        self.be_apubdef_user()
        response = self.client.get(reverse('intake-app_all_index'))
        self.assertContainsSubmissions(response, self.a_pubdef_submissions)
        self.assertContainsSubmissions(response, self.combo_submissions)
        self.assertNotContainsSubmissions(response, self.sf_pubdef_submissions)

    def test_that_cfa_user_can_see_apps_to_all_orgs(self):
        self.be_cfa_user()
        response = self.client.get(reverse('intake-app_all_index'))
        self.assertContainsSubmissions(response, self.submissions)

    def test_org_user_sees_name_of_org_in_index(self):
        user = self.be_ccpubdef_user()
        response = self.client.get(reverse('intake-app_all_index'))
        self.assertContains(response, user.profile.organization.name)

    def test_followup_staff_sees_notes(self):
        self.be_cfa_user()
        response = self.client.get(reverse('intake-app_all_index'))
        self.assertContains(response, "Save note")

    def test_contains_csv_download_link(self):
        self.be_apubdef_user()
        response = self.client.get(reverse('intake-app_all_index'))
        csv_download_link = reverse('intake-csv_download')
        self.assertContains(response, csv_download_link)

    def test_pdf_users_see_pdf_link(self):
        self.be_sfpubdef_user()
        # look for the pdf link of each app
        response = self.client.get(reverse('intake-app_all_index'))
        self.assertEqual(response.context_data['show_pdf'], True)
        for sub in self.sf_pubdef_submissions:
            pdf_url = reverse('intake-filled_pdf', kwargs=dict(
                submission_id=sub.id))
            self.assertContains(response, pdf_url)

    def test_non_pdf_users_dont_see_pdf_link(self):
        self.be_apubdef_user()
        # look for the pdf link of each app
        response = self.client.get(reverse('intake-app_all_index'))
        self.assertEqual(response.context_data['show_pdf'], False)
        for sub in self.combo_submissions:
            pdf_url = reverse('intake-filled_pdf', kwargs=dict(
                submission_id=sub.id))
            self.assertNotContains(response, pdf_url)

    def test_user_can_see_case_detail_printout_links(self):
        self.be_apubdef_user()
        response = self.client.get(reverse('intake-app_all_index'))
        for sub in self.a_pubdef_submissions:
            printout_url = html_utils.conditional_escape(
                sub.get_case_printout_url())
            self.assertContains(response, printout_url)

    def test_user_can_see_update_status_links(self):
        self.be_apubdef_user()
        response = self.client.get(reverse('intake-app_all_index'))
        for sub in self.a_pubdef_submissions:
            update_status_url = html_utils.conditional_escape(
                sub.get_case_update_status_url())
            self.assertContains(response, update_status_url)

    def test_that_nonstaff_cfa_user_cant_see_apps(self):
        self.be_monitor_user()
        response = self.client.get(reverse('intake-app_all_index'))
        self.assertEqual(response.status_code, 302)

    def test_org_user_can_see_latest_status_of_app(self):
        user = self.be_apubdef_user()
        response = self.client.get(reverse('intake-app_all_index'))
        for sub in self.a_pubdef_submissions:

            status_update = sub.applications.filter(
                organization=user.profile.organization).first(
            ).status_updates.order_by('-updated').first()
            if status_update:
                status = status_update.status_type.display_name
            else:
                status = 'Unread'
            self.assertContains(
                response, html_utils.conditional_escape(status))

    def test_outgoing_transfers_appear_without_update_status_button(self):
        self.be_apubdef_user()
        response = self.client.get(reverse('intake-app_all_index'))
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
        outgoing_transfer_rows = soup.find_all(class_="outgoing-transfer")
        self.assertTrue(len(outgoing_transfer_rows))
        for row in outgoing_transfer_rows:
            html_text = str(row)
            self.assertNotIn('Update Status', html_text)
            self.assertIn('Transferred', html_text)

    def test_incoming_transfers_have_status_button_and_transfer_label(self):
        self.be_apubdef_user()
        response = self.client.get(reverse('intake-app_all_index'))
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
        incoming_transfer_rows = soup.find_all(class_="incoming-transfer")
        self.assertTrue(len(incoming_transfer_rows))
        for row in incoming_transfer_rows:
            html_text = str(row)
            self.assertIn('Update Status', html_text)
            self.assertIn('(Incoming Transfer)', html_text)
            self.assertIn('Unread', html_text)


class TestApplicationUnreadIndex(TestCase):
    fixtures = ['counties', 'organizations', 'groups']
    view_name = 'intake-app_unread_index'

    def test_does_not_show_csv_download_link(self):
        profile = app_reviewer('cc_pubdef')
        make_apps_for('cc_pubdef', count=1)
        self.client.login(
            username=profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(reverse(self.view_name))
        csv_download_link = reverse('intake-csv_download')
        self.assertNotContains(response, csv_download_link)


class TestApplicationNeedsUpdateIndex(TestCase):
    fixtures = ['counties', 'organizations', 'groups']
    view_name = 'intake-app_needs_update_index'

    def test_does_not_show_csv_download_link(self):
        profile = app_reviewer('cc_pubdef')
        make_apps_for('cc_pubdef', count=1)
        self.client.login(
            username=profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(reverse(self.view_name))
        csv_download_link = reverse('intake-csv_download')
        self.assertNotContains(response, csv_download_link)


class TestApplicationCountyNotListedIndex(TestCase):
    fixtures = ['counties', 'organizations', 'groups']

    def test_anon_user_is_redirected_to_login(self):
        response = self.client.get(reverse('intake-app_cnl_index'))
        self.assertRedirects(
            response,
            '{}?next={}'.format(
                reverse('user_accounts-login'),
                reverse('intake-app_cnl_index')))

    def test_followup_user_can_access(self):
        profile = followup_user()
        self.client.login(
            username=profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(reverse('intake-app_cnl_index'))
        self.assertEqual(200, response.status_code)

    def test_org_user_is_redirected_to_profile(self):
        profile = app_reviewer()
        self.client.login(
            username=profile.user.username,
            password=settings.TEST_USER_PASSWORD)
        response = self.client.get(reverse('intake-app_cnl_index'))
        self.assertRedirects(response, reverse('user_accounts-profile'))


class TestApplicationBundleDetail(IntakeDataTestCase):

    fixtures = [
        'counties', 'groups',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_sf_pubdef', 'template_options',
        'mock_1_submission_to_multiple_orgs',
        'mock_1_bundle_to_a_pubdef'
    ]

    def test_returns_200_on_existing_bundle_id(self):
        """`ApplicationBundleDetailView` return `OK` for existing bundle

        create an `ApplicationBundle`,
        try to access `ApplicationBundleDetailView` using `id`
        assert that 200 OK is returned
        """
        self.be_apubdef_user()
        with self.assertLogs(
                'project.services.logging_service', logging.INFO) as logs:
            result = self.client.get(reverse(
                'intake-app_bundle_detail',
                kwargs=dict(bundle_id=self.a_pubdef_bundle.id)))
        self.assertEqual(result.status_code, 200)
        assertInLogsCount(logs, {
            'app_bundle_opened': self.a_pubdef_bundle.submissions.count()})

    def test_staff_user_gets_200(self):
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

    def test_user_from_wrong_org_is_redirected_to_profile(self):
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
            result, reverse('user_accounts-profile'),
            fetch_redirect_response=False)

    def test_has_pdf_bundle_url_if_needed(self):
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

    def test_agency_user_can_see_transfer_action_links(self):
        self.be_apubdef_user()
        response = self.client.get(
            self.a_pubdef_bundle.get_absolute_url())
        for sub in self.a_pubdef_submissions:
            transfer_action_url = html_utils.conditional_escape(
                sub.get_transfer_action(response.wsgi_request)['url'])
            self.assertContains(response, transfer_action_url)

    def test_user_can_see_app_bundle_printout_link(self):
        self.be_apubdef_user()
        response = self.client.get(self.a_pubdef_bundle.get_absolute_url())
        printout_url = html_utils.conditional_escape(
            self.a_pubdef_bundle.get_printout_url())
        self.assertContains(response, printout_url)

    def test_marks_apps_as_opened(self):
        user = self.be_apubdef_user()
        self.client.get(self.a_pubdef_bundle.get_absolute_url())
        apps = models.Application.objects.filter(
            organization=user.profile.organization,
            form_submission__id__in=[
                sub.id for sub in self.a_pubdef_bundle.submissions.all()])
        self.assertTrue(all([app.has_been_opened for app in apps]))


@skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
class TestApplicationBundleDetailPDFView(IntakeDataTestCase):
    fixtures = [
        'counties', 'groups',
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

    def test_marks_apps_as_opened(self):
        user = self.be_sfpubdef_user()
        self.client.get(self.bundle.get_pdf_bundle_url())
        apps = models.Application.objects.filter(
            organization=user.profile.organization,
            form_submission__id__in=[
                sub.id for sub in self.bundle.submissions.all()])
        self.assertTrue(all([app.has_been_opened for app in apps]))


class TestCaseBundlePrintoutPDFView(IntakeDataTestCase):

    fixtures = TestApplicationDetail.fixtures + [
        'mock_1_bundle_to_a_pubdef']

    def test_anonymous_users_redirected_to_login(self):
        self.be_anonymous()
        bundle = models.ApplicationBundle.objects.first()
        response = self.client.get(
            reverse(
                'intake-case_bundle_printout',
                kwargs=dict(bundle_id=bundle.id)))
        self.assertIn(reverse('user_accounts-login'), response.url)
        self.assertEqual(response.status_code, 302)

    def test_users_from_wrong_org_redirected_to_profile(self):
        self.be_ccpubdef_user()
        bundle = models.ApplicationBundle.objects.filter(
            organization__slug__contains='a_pubdef').first()
        response = self.client.get(
            reverse(
                'intake-case_bundle_printout',
                kwargs=dict(bundle_id=bundle.id)))
        self.assertRedirects(response, reverse('user_accounts-profile'))

    def test_marks_apps_as_opened(self):
        user = self.be_apubdef_user()
        bundle = models.ApplicationBundle.objects.filter(
            organization__slug__contains='a_pubdef').first()
        self.client.get(
            reverse(
                'intake-case_bundle_printout',
                kwargs=dict(bundle_id=bundle.id)))
        apps = models.Application.objects.filter(
            organization=user.profile.organization,
            form_submission__id__in=[
                sub.id for sub in bundle.submissions.all()])
        self.assertTrue(all([app.has_been_opened for app in apps]))
