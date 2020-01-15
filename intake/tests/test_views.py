
from unittest import skipUnless
from unittest.mock import patch
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from intake.tests import mock, factories
from intake.tests.base_testcases import IntakeDataTestCase, DELUXE_TEST
from intake import models, constants
from formation import fields
from formation.field_types import YES
from project.jinja2 import url_with_ids

import intake.services.bundles as BundlesService


class TestViews(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations',
        'groups',
        'mock_profiles',
        'mock_2_submissions_to_sf_pubdef', 'template_options']

    def set_session_counties(self, counties=None):
        if not counties:
            counties = [constants.Counties.SAN_FRANCISCO]
        self.set_session(form_in_progress={'counties': counties})

    def test_home_view(self):
        response = self.client.get(reverse('intake-home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Clear My Record', response.content.decode('utf-8'))

    def test_confirm_view(self):
        self.be_anonymous()
        applicant = factories.ApplicantFactory.create()
        base_data = dict(
            counties=['sanfrancisco'],
            **mock.NEW_RAW_FORM_DATA)
        self.set_session(
            form_in_progress=base_data,
            applicant_id=applicant.id)
        response = self.client.get(reverse('intake-confirm'))
        self.assertContains(response, base_data['first_name'][0])
        self.assertContains(response, base_data['last_name'][0])
        self.assertContains(
            response,
            fields.AddressField.is_recommended_error_message)
        self.assertContains(
            response,
            fields.SocialSecurityNumberField.is_recommended_error_message)
        self.assertContains(
            response,
            fields.DateOfBirthField.is_recommended_error_message)

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
    def test_authenticated_user_can_see_filled_pdf(self):
        self.be_sfpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        filled_pdf_bytes = self.fillable.fill(submission)
        pdf_file = SimpleUploadedFile('filled.pdf', filled_pdf_bytes,
                                      content_type='application/pdf')
        filled_pdf_model = models.FilledPDF(
            original_pdf=self.fillable,
            submission=submission,
            pdf=pdf_file
        )
        filled_pdf_model.save()
        pdf = self.client.get(reverse('intake-filled_pdf',
                                      kwargs=dict(
                                          submission_id=submission.id
                                      )))
        self.assertTrue(len(pdf.content) > 69000)
        self.assertEqual(type(pdf.content), bytes)

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
    @patch('intake.notifications.slack_simple.send')
    def test_authenticated_user_can_get_filled_pdf_without_building(
            self, slack_simple):
        """
        test_authenticated_user_can_get_filled_pdf_without_building

        this tests that a pdf will be served even if not pregenerated
        """
        self.be_sfpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        pdf = self.client.get(reverse('intake-filled_pdf',
                                      kwargs=dict(
                                          submission_id=submission.id
                                      )))
        self.assertTrue(len(pdf.content) > 69000)
        self.assertEqual(type(pdf.content), bytes)

    def test_authenticated_user_can_see_list_of_submitted_apps(self):
        self.be_cfa_user()
        index = self.client.get(reverse('intake-app_index'))
        for submission in models.FormSubmission.objects.all():
            self.assertContains(
                index,
                submission.get_absolute_url())

    def test_anonymous_user_cannot_see_filled_pdfs(self):
        self.be_anonymous()
        pdf = self.client.get(reverse('intake-filled_pdf',
                                      kwargs=dict(
                                          submission_id=1
                                      )))
        self.assertRedirects(
            pdf,
            "{}?next={}".format(
                reverse('user_accounts-login'),
                reverse('intake-filled_pdf', kwargs={'submission_id': 1})),
            fetch_redirect_response=False
        )

    def test_anonymous_user_cannot_see_submitted_apps(self):
        self.be_anonymous()
        index = self.client.get(reverse('intake-app_index'))
        self.assertRedirects(index,
                             "{}?next={}".format(
                                 reverse('user_accounts-login'),
                                 reverse('intake-app_index')
                             )
                             )

    def test_old_urls_return_permanent_redirect(self):
        # redirecting the auth views does not seem necessary
        redirects = {
            '/sanfrancisco/': reverse('intake-apply'),
            '/sanfrancisco/applications/': reverse('intake-app_index'),
        }

        # redirecting the action views (add) does not seem necessary
        id_redirects = {'/sanfrancisco/{}/': 'intake-filled_pdf'}
        multi_id_redirects = {
            '/sanfrancisco/bundle/{}': 'intake-app_bundle',
            '/sanfrancisco/pdfs/{}': 'intake-pdf_bundle'}

        # make some old apps with ids
        old_uuids = [
            '0efd75e8721c4308a8f3247a8c63305d',
            'b873c4ceb1cd4939b1d4c890997ef29c',
            '6cb3887be35543c4b13f27bf83219f4f']
        key_params = '?keys=' + '|'.join(old_uuids)
        ported_models = []
        for uuid in old_uuids:
            instance = factories.FormSubmissionFactory.create(
                old_uuid=uuid)
            ported_models.append(instance)
        ported_models_query = models.FormSubmission.objects.filter(
            old_uuid__in=old_uuids)

        for old, new in redirects.items():
            response = self.client.get(old)
            self.assertRedirects(
                response, new,
                status_code=301, fetch_redirect_response=False)

        for old_template, new_view in id_redirects.items():
            old = old_template.format(old_uuids[2])
            response = self.client.get(old)
            new = reverse(
                new_view, kwargs=dict(
                    submission_id=ported_models[2].id))
            self.assertRedirects(
                response, new,
                status_code=301, fetch_redirect_response=False)

        for old_template, new_view in multi_id_redirects.items():
            old = old_template.format(key_params)
            response = self.client.get(old)
            new = url_with_ids(new_view, [s.id for s in ported_models_query])
            self.assertRedirects(
                response, new,
                status_code=301, fetch_redirect_response=False)
