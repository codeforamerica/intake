from unittest import skipIf
from django.test import TestCase
from user_accounts.tests.test_auth_integration import AuthIntegrationTestCase
from django.core.urlresolvers import reverse

from intake.tests import mock

from intake.views import add_ids_as_params

class TestViews(AuthIntegrationTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.have_four_submissions()
        cls.have_a_fillable_pdf()

    @classmethod
    def have_four_submissions(cls):
        cls.submissions = mock.FormSubmissionFactory.create_batch(4)

    @classmethod
    def have_a_fillable_pdf(cls):
        cls.fillable = mock.fillable_pdf()

    def test_home_view(self):
        response = self.client.get(reverse('intake-home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Clear My Record', response.content.decode('utf-8'))

    def test_apply_view(self):
        response = self.client.get(reverse('intake-apply'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Apply to Clear My Record', response.content.decode('utf-8'))

    def test_anonymous_user_can_fill_out_app_and_reach_thanks_page(self):
        self.be_anonymous()
        result = self.client.fill_form(
            reverse('intake-apply'),
            first_name="Anonymous"
            )
        self.assertRedirects(result, 
            reverse('intake-thanks'))
        thanks_page = self.client.get(result.url)
        self.assertContains(thanks_page, "Thank")

    def test_authenticated_user_can_see_filled_pdf(self):
        self.be_regular_user()
        pdf = self.client.get(reverse('intake-filled_pdf',
            kwargs=dict(
                submission_id=self.submissions[0].id
                )))
        self.assertTrue(len(pdf.content) > 69000)
        self.assertEqual(type(pdf.content), bytes)

    def test_authenticated_user_can_see_list_of_submitted_apps(self):
        self.be_regular_user()
        index = self.client.get(reverse('intake-app_index'))
        for submission in self.submissions:
            self.assertContains(index, submission.answers['last_name'])

    def test_anonymous_user_cannot_see_filled_pdfs(self):
        self.be_anonymous()
        pdf = self.client.get(reverse('intake-filled_pdf',
            kwargs=dict(
                submission_id=self.submissions[0].id
                )))
        self.assertRedirects(pdf, 
            "{}?next={}".format(
            reverse('user_accounts-login'),
            reverse('intake-filled_pdf', kwargs={
                'submission_id': self.submissions[0].id})))

    def test_anonymous_user_cannot_see_submitted_apps(self):
        self.be_anonymous()
        index = self.client.get(reverse('intake-app_index'))
        self.assertRedirects(index,
            "{}?next={}".format(
            reverse('user_accounts-login'),
            reverse('intake-app_index')
                )
            )

    def test_authenticated_user_can_see_pdf_bundle(self):
        self.be_regular_user()
        ids = [s.id for s in self.submissions]
        url = add_ids_as_params(
            reverse('intake-pdf_bundle'), ids)
        bundle = self.client.get(url)
        self.assertEqual(bundle.status_code, 200)

    @skipIf(True, "not yet implemented")
    def test_authenticated_user_can_see_app_bundle(self):
        self.be_regular_user()
        bundle = self.client.get(
            reverse('intake-app_bundle'))
        self.assertEqual(bundle.status_code, 200)

    @skipIf(True, "not yet implemented")
    def test_authenticated_user_cannot_see_apps_to_other_org(self):
        pass

    @skipIf(True, "not yet implemented")
    def test_authenticated_user_can_delete_apps(self):
        pass

    @skipIf(True, "not yet implemented")
    def test_old_urls_permanently_redirect_to_new_urls(self):
        pass

