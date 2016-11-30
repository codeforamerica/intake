import os
import random
import logging
from unittest import skipUnless
from unittest.mock import patch, Mock
from django.test import TestCase, override_settings
from user_accounts.tests.test_auth_integration import AuthIntegrationTestCase
from django.db.models import Count
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import html as html_utils

from intake.tests import mock
from intake.tests.base_testcases import IntakeDataTestCase, DELUXE_TEST
from intake import models, constants
from intake.views import session_view_base, application_form_views
from user_accounts import models as auth_models
from formation import fields, forms

from project.jinja2 import url_with_ids


class TestViews(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations',
        'mock_profiles',
        'mock_2_submissions_to_sf_pubdef']

    def set_session_counties(self, counties=None):
        if not counties:
            counties = [constants.Counties.SAN_FRANCISCO]
        self.set_session(form_in_progress={
            'counties': counties})

    def test_home_view(self):
        response = self.client.get(reverse('intake-home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Clear My Record', response.content.decode('utf-8'))

    def test_apply_view(self):
        self.set_session_counties()
        response = self.client.get(reverse('intake-county_application'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Apply to Clear My Record',
                      response.content.decode('utf-8'))
        self.assertNotContains(response, "This field is required.")
        self.assertNotContains(response, "warninglist")

    def test_confirm_view(self):
        self.be_anonymous()
        base_data = dict(
            counties=['sanfrancisco'],
            **mock.NEW_RAW_FORM_DATA)
        self.set_session(
            form_in_progress=base_data)
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

    @patch('intake.models.get_parser')
    @patch(
        'intake.views.application_form_views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.session_view_base.notifications.slack_new_submission.send')
    def test_anonymous_user_can_fill_out_app_and_reach_thanks_page(
            self, slack, send_confirmation, get_parser):
        get_parser.return_value.fill_pdf.return_value = b'a pdf'
        self.be_anonymous()
        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=['sanfrancisco']
        )
        self.assertRedirects(result, reverse('intake-county_application'))
        result = self.client.fill_form(
            reverse('intake-county_application'),
            first_name="Anonymous",
            last_name="Anderson",
            ssn='123091203',
            **{
                'dob.day': '10',
                'dob.month': '10',
                'dob.year': '80',
                'address.street': '100 Market St',
                'address.city': 'San Francisco',
                'address.state': 'CA',
                'address.zip': '99999',
            })
        self.assertRedirects(result, reverse('intake-thanks'))
        thanks_page = self.client.get(result.url)
        filled_pdf = models.FilledPDF.objects.first()
        self.assertTrue(filled_pdf)
        self.assertTrue(filled_pdf.pdf)
        self.assertNotEqual(filled_pdf.pdf.size, 0)
        submission = models.FormSubmission.objects.order_by('-pk').first()
        self.assertEqual(filled_pdf.submission, submission)
        organization = submission.organizations.first()
        self.assertEqual(filled_pdf.original_pdf, organization.pdfs.first())
        self.assertContains(thanks_page, "Thank")
        self.assert_called_once_with_types(
            slack,
            submission='FormSubmission',
            request='WSGIRequest',
            submission_count='int')
        send_confirmation.assert_called_once_with()

    @patch('intake.models.get_parser')
    @patch(
        'intake.views.application_form_views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.session_view_base.notifications.slack_new_submission.send')
    def test_apply_with_name_only(self, slack, send_confirmation, get_parser):
        get_parser.return_value.fill_pdf.return_value = b'a pdf'
        self.be_anonymous()
        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=['sanfrancisco'],
            follow=True
        )
        # this should raise warnings
        result = self.client.fill_form(
            reverse('intake-county_application'),
            first_name="Foo",
            last_name="Bar"
        )
        self.assertRedirects(
            result, reverse('intake-confirm'), fetch_redirect_response=False)
        result = self.client.get(result.url)
        self.assertContains(result, "Foo")
        self.assertContains(result, "Bar")
        self.assertContains(
            result, fields.AddressField.is_recommended_error_message)
        self.assertContains(
            result,
            fields.SocialSecurityNumberField.is_recommended_error_message)
        self.assertContains(
            result, fields.DateOfBirthField.is_recommended_error_message)
        self.assertContains(
            result, application_form_views.Confirm.incoming_message)
        slack.assert_not_called()
        result = self.client.fill_form(
            reverse('intake-confirm'),
            first_name="Foo",
            last_name="Bar",
            follow=True
        )
        self.assertEqual(result.wsgi_request.path, reverse('intake-thanks'))
        self.assert_called_once_with_types(
            slack,
            submission='FormSubmission',
            request='WSGIRequest',
            submission_count='int')
        send_confirmation.assert_called_once_with()

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_authenticated_user_can_see_filled_pdf(self, slack):
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
    @patch('intake.notifications.slack_submissions_viewed.send')
    @patch('intake.notifications.slack_simple.send')
    def test_authenticated_user_can_get_filled_pdf_without_building(
            self, slack_simple, slack_viewed):
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

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
    @patch('intake.notifications.slack_simple.send')
    def test_authenticated_user_can_see_pdf_bundle(self, slack):
        self.be_sfpubdef_user()
        ids = models.FormSubmission.objects.filter(
            organizations=self.sf_pubdef).values_list('pk', flat=True)
        url = url_with_ids('intake-pdf_bundle', ids)
        bundle = self.client.get(url, follow=True)
        self.assertEqual(bundle.status_code, 200)

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
    @patch('intake.notifications.slack_simple.send')
    def test_staff_user_can_see_pdf_bundle(self, slack):
        self.be_cfa_user()
        submissions = self.sf_pubdef_submissions
        bundle = models.ApplicationBundle.create_with_submissions(
            submissions=submissions,
            organization=self.sf_pubdef)
        ids = [s.id for s in submissions]
        url = url_with_ids('intake-pdf_bundle', ids)
        response = self.client.get(url)
        self.assertRedirects(response, bundle.get_pdf_bundle_url())
        pdf_response = self.client.get(response.url)
        self.assertEqual(pdf_response.status_code, 200)

    @patch('intake.notifications.slack_submissions_viewed.send')
    def test_authenticated_user_can_see_app_bundle(self, slack):
        self.be_cfa_user()
        submissions = self.submissions
        ids = [s.id for s in submissions]
        url = url_with_ids('intake-app_bundle', ids)
        bundle = self.client.get(url)
        self.assertEqual(bundle.status_code, 200)

    @patch('intake.views.session_view_base.notifications.slack_submissions_deleted.send')
    def test_authenticated_user_can_delete_apps(self, slack):
        self.be_cfa_user()
        submission = self.submissions[0]
        pdf_link = reverse('intake-filled_pdf',
                           kwargs={'submission_id': submission.id})
        url = reverse('intake-delete_page',
                      kwargs={'submission_id': submission.id})
        delete_page = self.client.get(url)
        self.assertEqual(delete_page.status_code, 200)
        after_delete = self.client.fill_form(url)
        self.assertRedirects(after_delete, reverse('intake-app_index'))
        index = self.client.get(after_delete.url)
        self.assertNotContains(index, pdf_link)

    @patch('intake.views.session_view_base.notifications.slack_submissions_processed.send')
    def test_agency_user_can_mark_apps_as_processed(self, slack):
        self.be_sfpubdef_user()
        submissions = self.sf_pubdef_submissions
        ids = [s.id for s in submissions]
        mark_link = url_with_ids('intake-mark_processed', ids)
        marked = self.client.get(mark_link)
        self.assert_called_once_with_types(
            slack,
            submissions='list',
            user='User')
        self.assertRedirects(marked, reverse('intake-app_index'))
        args, kwargs = slack.call_args
        for sub in kwargs['submissions']:
            self.assertTrue(sub.last_processed_by_agency())
            self.assertIn(sub.id, ids)

    def test_old_urls_return_permanent_redirect(self):
        # redirecting the auth views does not seem necessary
        redirects = {
            '/sanfrancisco/': reverse('intake-apply'),
            '/sanfrancisco/applications/': reverse('intake-app_index'),
        }

        # redirecting the action views (delete, add) does not seem necessary
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
            instance = mock.FormSubmissionFactory.create(
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


class TestPartnerListView(TestCase):
    fixtures = ['counties', 'organizations']

    def test_returns_200_with_org_name_list(self):
        response = self.client.get(reverse('intake-partner_list'))
        orgs = auth_models.Organization.objects.filter(
            is_receiving_agency=True)
        self.assertEqual(response.status_code, 200)
        for org in orgs:
            self.assertContains(
                response, html_utils.conditional_escape(org.name))


class TestPartnerDetailView(TestCase):
    fixtures = ['counties', 'organizations']

    def test_returns_200_with_org_details(self):
        sf_pubdef = auth_models.Organization.objects.get(
            slug=constants.Organizations.SF_PUBDEF)
        response = self.client.get(
            reverse(
                'intake-partner_detail',
                kwargs=dict(organization_slug=sf_pubdef.slug)
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, sf_pubdef.phone_number)
        self.assertContains(response, html_utils.escape(sf_pubdef.blurb))
        self.assertContains(response, sf_pubdef.name)


@override_settings(MIXPANEL_KEY='fake_key')
class TestRAPSheetInstructions(TestCase):

    def test_renders_with_no_session_data(self):
        response = self.client.get(reverse('intake-rap_sheet'))
        # make sure it has a link to the pdf
        self.assertNotIn('qualifies_for_fee_waiver', response.context_data)
        # make sure there aren't any unrendered variables
        self.assertNotContains(response, "{{")


    @patch('intake.views.application_form_views.get_last_submission_of_applicant')
    @patch('intake.views.application_form_views.RAPSheetInstructions.get_applicant_id')
    def test_pulls_relevant_info_if_session_data(self, get_app_id, get_sub):
        get_app_id.return_value = 1
        submission_mock = Mock()
        submission_mock.organizations.all.return_value = [
            'an_org', 'another_org']
        get_sub.return_value = submission_mock
        response = self.client.get(reverse('intake-rap_sheet'))
        self.assertIn('qualifies_for_fee_waiver', response.context_data)
        self.assertIn('organizations', response.context_data)
        submission_mock.qualifies_for_fee_waiver.assert_called_once_with()


class TestSelectCountyView(AuthIntegrationTestCase):

    def test_anonymous_user_can_access_county_view(self):
        self.be_anonymous()
        county_view = self.client.get(
            reverse('intake-apply'))
        for slug, description in constants.COUNTY_CHOICES:
            self.assertContains(county_view, slug)
            self.assertContains(county_view, html_utils.escape(description))

        applicant_id = self.client.session.get('applicant_id')
        self.assertIsNone(applicant_id)

    def test_anonymous_user_can_submit_county_selection(self):
        self.be_anonymous()
        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=['contracosta'],
            headers={'HTTP_USER_AGENT': 'tester'})
        self.assertRedirects(result, reverse('intake-county_application'))
        applicant_id = self.client.session.get('applicant_id')
        self.assertTrue(applicant_id)
        applicant = models.Applicant.objects.get(id=applicant_id)
        self.assertTrue(applicant)
        self.assertTrue(applicant.visitor_id)
        visitor = models.Visitor.objects.get(id=applicant.visitor_id)
        self.assertTrue(visitor)
        events = list(applicant.events.all())
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.name,
                         models.ApplicationEvent.APPLICATION_STARTED)
        self.assertIn('ip', event.data)
        self.assertIn('user_agent', event.data)
        self.assertEqual(event.data['user_agent'], 'tester')
        self.assertIn('referrer', event.data)
        self.assertEqual(event.data['counties'], ['contracosta'])

    def test_anonymous_user_cannot_submit_empty_county_selection(self):
        self.be_anonymous()
        result = self.client.fill_form(
            reverse('intake-apply'))
        self.assertEqual(result.status_code, 200)
        form = result.context_data['form']
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)


class TestMultiCountyApplication(AuthIntegrationTestCase):

    fixtures = ['counties', 'organizations']

    @patch(
        'intake.views.application_form_views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.session_view_base.notifications.slack_new_submission.send')
    def test_sf_application_redirects_if_missing_recommended_fields(
            self, slack, send_confirmation):
        self.be_anonymous()
        applicant = models.Applicant()
        applicant.save()
        sanfrancisco = constants.Counties.SAN_FRANCISCO
        sf_pubdef = constants.Organizations.SF_PUBDEF
        answers = mock.fake.sf_county_form_answers()
        answers['ssn'] = ''
        self.set_session(
            form_in_progress=dict(counties=[sanfrancisco]),
            applicant_id=applicant.id
            )
        response = self.client.fill_form(
            reverse('intake-county_application'),
            follow=True,
            **answers
            )
        self.assertEqual(
            response.wsgi_request.path, reverse('intake-confirm'))
        form = response.context_data['form']
        self.assertTrue(form.warnings)
        self.assertFalse(form.errors)
        self.assertIn('ssn', form.warnings)
        slack.assert_not_called()
        send_confirmation.assert_not_called()
        submitted_event_count = applicant.events.filter(
            name=models.ApplicationEvent.APPLICATION_SUBMITTED).count()
        self.assertEqual(0, submitted_event_count)

    @patch(
        'intake.views.application_form_views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.session_view_base.notifications.slack_new_submission.send')
    def test_can_apply_to_contra_costa_alone(self, slack, send_confirmation):
        self.be_anonymous()
        contracosta = constants.Counties.CONTRA_COSTA
        cc_pubdef = constants.Organizations.COCO_PUBDEF
        answers = mock.fake.contra_costa_county_form_answers()

        county_fields = forms.ContraCostaFormSpec.fields
        other_county_fields = \
            forms.SanFranciscoCountyFormSpec.fields \
            | forms.OtherCountyFormSpec.fields
        county_specific_fields = county_fields - other_county_fields
        county_specific_field_names = [
            Field.context_key for Field in county_specific_fields]
        other_county_fields = other_county_fields - county_fields
        other_county_field_names = [
            Field.context_key for Field in other_county_fields]

        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=[contracosta])
        self.assertRedirects(result, reverse('intake-county_application'))
        result = self.client.get(reverse('intake-county_application'))

        for field_name in county_specific_field_names:
            self.assertContains(result, field_name)

        for field_name in other_county_field_names:
            self.assertNotContains(result, field_name)

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)
        self.assertRedirects(result, reverse('intake-thanks'))
        applicant_id = self.client.session.get('applicant_id')
        self.assertTrue(applicant_id)
        applicant = models.Applicant.objects.get(id=applicant_id)

        submissions = list(applicant.form_submissions.all())
        self.assertEqual(1, len(submissions))
        submission = submissions[0]

        county_slugs = [county.slug for county in submission.get_counties()]
        self.assertListEqual(county_slugs, [contracosta])
        org_slugs = [org.slug for org in submission.organizations.all()]
        self.assertListEqual(org_slugs, [cc_pubdef])

        submitted_event_count = applicant.events.filter(
            name=models.ApplicationEvent.APPLICATION_SUBMITTED).count()

        self.assertEqual(1, submitted_event_count)

    @patch(
        'intake.views.application_form_views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.session_view_base.notifications.slack_new_submission.send')
    def test_contra_costa_errors_properly(self, slack, send_confirmation):
        self.be_anonymous()
        contracosta = constants.Counties.CONTRA_COSTA
        answers = mock.fake.contra_costa_county_form_answers()
        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=[contracosta])
        required_fields = forms.ContraCostaFormSpec.required_fields

        # check that leaving out any required field returns an error on that
        # field
        for required_field in required_fields:
            if hasattr(required_field, 'subfields'):
                continue
            field_key = required_field.context_key
            bad_data = answers.copy()
            bad_data[field_key] = ''
            result = self.client.fill_form(
                reverse('intake-county_application'),
                **bad_data)
            self.assertContains(
                result, required_field.is_required_error_message)

        # check for the preferred contact methods validator
        bad_data = answers.copy()
        bad_data['contact_preferences'] = ['prefers_email', 'prefers_sms']
        bad_data['email'] = ''
        bad_data['phone_number'] = ''
        result = self.client.fill_form(
            reverse('intake-county_application'),
            **bad_data)
        self.assertTrue(result.context_data['form'].email.errors)
        self.assertTrue(result.context_data['form'].phone_number.errors)

        event = models.ApplicationEvent.objects.filter(
            applicant_id=self.client.session['applicant_id'],
            name=models.ApplicationEvent.APPLICATION_ERRORS).first()

        self.assertDictEqual(
            result.context_data['form'].get_serialized_errors(),
            event.data['errors'])

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)
        self.assertRedirects(result, reverse('intake-thanks'))
        self.assertTrue(slack.called)
        self.assertTrue(send_confirmation.called)

    @patch(
        'intake.views.application_form_views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.session_view_base.notifications.slack_new_submission.send')
    def test_alameda_pubdef_application_redirects_to_declaration_letter(
            self, slack, send_confirmation):

        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        answers = mock.fake.alameda_pubdef_answers()
        result = self.client.fill_form(
            reverse('intake-apply'), counties=[alameda])
        self.assertRedirects(result, reverse('intake-county_application'))
        result = self.client.get(reverse('intake-county_application'))

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)

        self.assertRedirects(result, reverse("intake-write_letter"))
        slack.assert_not_called()
        send_confirmation.assert_not_called()

    @patch(
        'intake.views.application_form_views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.session_view_base.notifications.slack_new_submission.send')
    def test_invalid_alameda_application_returns_same_page_with_error(
            self, slack, send_confirmation):
        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        answers = mock.fake.alameda_pubdef_answers()
        answers['monthly_income'] = ""
        result = self.client.fill_form(
            reverse('intake-apply'), counties=[alameda])
        self.assertRedirects(result, reverse('intake-county_application'))
        result = self.client.get(reverse('intake-county_application'))

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.wsgi_request.path,
                         reverse('intake-county_application'))
        self.assertTrue(result.context_data['form'].errors)
        slack.assert_not_called()
        send_confirmation.assert_not_called()

        event = models.ApplicationEvent.objects.filter(
            applicant_id=self.client.session['applicant_id'],
            name=models.ApplicationEvent.APPLICATION_ERRORS).first()

        self.assertDictEqual(
            result.context_data['form'].get_serialized_errors(),
            event.data['errors'])

    @patch(
        'intake.views.application_form_views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.session_view_base.notifications.slack_new_submission.send')
    def test_valid_ebclc_application_returns_rap_sheet_page(
            self, slack, send_confirmation):
        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        answers = mock.fake.ebclc_answers()
        result = self.client.fill_form(
            reverse('intake-apply'), counties=[alameda])
        self.assertRedirects(result, reverse('intake-county_application'))
        result = self.client.get(reverse('intake-county_application'))

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)
        self.assertRedirects(
            result, reverse("intake-rap_sheet"))
        self.assertTrue(slack.called)
        self.assertTrue(send_confirmation.called)

    @patch(
        'intake.views.application_form_views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.session_view_base.notifications.slack_new_submission.send')
    def test_invalid_ebclc_application_returns_same_page_with_error(
            self, slack, send_confirmation):
        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        answers = mock.fake.ebclc_answers()
        answers['monthly_income'] = ""
        result = self.client.fill_form(
            reverse('intake-apply'), counties=[alameda])
        self.assertRedirects(result, reverse('intake-county_application'))
        result = self.client.get(reverse('intake-county_application'))

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.wsgi_request.path,
                         reverse('intake-county_application'))
        self.assertTrue(result.context_data['form'].errors)
        slack.assert_not_called()
        send_confirmation.assert_not_called()

        event = models.ApplicationEvent.objects.filter(
            applicant_id=self.client.session['applicant_id'],
            name=models.ApplicationEvent.APPLICATION_ERRORS).first()

        self.assertDictEqual(
            result.context_data['form'].get_serialized_errors(),
            event.data['errors'])

    def test_can_go_back_and_reset_counties(self):
        self.be_anonymous()
        county_slugs = [slug for slug, text in constants.COUNTY_CHOICES]
        first_choices = random.sample(county_slugs, 2)
        second_choices = [random.choice(county_slugs)]
        self.client.fill_form(
            reverse('intake-apply'),
            counties=first_choices,
            follow=True)
        county_setting = self.client.session['form_in_progress']['counties']
        self.assertEqual(county_setting, first_choices)

        self.client.fill_form(
            reverse('intake-apply'),
            counties=second_choices,
            follow=True)
        county_setting = self.client.session['form_in_progress']['counties']
        self.assertEqual(county_setting, second_choices)

    @patch('intake.notifications.slack_simple.send')
    def test_no_counties_found_error_sends_slack_and_redirects(self, slack):
        self.be_anonymous()
        response = self.client.get(reverse('intake-county_application'))
        self.assertRedirects(
            response, reverse('intake-home'), fetch_redirect_response=False)
        self.assertTrue(slack.called)
        response = self.client.get(response.url)
        expected_flash_message = html_utils.conditional_escape(
            session_view_base.GENERIC_USER_ERROR_MESSAGE)
        self.assertContains(response, expected_flash_message)


class TestDeclarationLetterView(AuthIntegrationTestCase):

    fixtures = ['counties', 'organizations', 'mock_profiles']

    @patch(
        'intake.views.application_form_views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.session_view_base.notifications.slack_new_submission.send')
    def test_expected_success(self, slack, send_confirmation):
        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        self.client.fill_form(
            reverse('intake-apply'), counties=[alameda], follow=True)
        answers = mock.fake.alameda_pubdef_answers(first_name="RandomName")
        self.client.fill_form(
            reverse('intake-county_application'), follow=True, **answers)

        declaration_answers = mock.fake.declaration_letter_answers()
        result = self.client.fill_form(
            reverse('intake-write_letter'), **declaration_answers)

        self.assertRedirects(result, reverse('intake-review_letter'))

        form_data = self.client.session.get('form_in_progress')
        for key, value in declaration_answers.items():
            self.assertIn(key, form_data)
            session_value = form_data[key]
            self.assertEqual(session_value, value)

        slack.assert_not_called()
        send_confirmation.assert_not_called()

    @patch(
        'intake.views.application_form_views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.session_view_base.notifications.slack_new_submission.send')
    def test_invalid_letter_returns_same_page(self, slack, send_confirmation):
        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        self.client.fill_form(
            reverse('intake-apply'), counties=[alameda], follow=True)
        answers = mock.fake.alameda_pubdef_answers(first_name="RandomName")
        self.client.fill_form(
            reverse('intake-county_application'), follow=True, **answers)

        slack.assert_not_called()
        send_confirmation.assert_not_called()

        declaration_answers = mock.fake.declaration_letter_answers(
            declaration_letter_why="")

        result = self.client.fill_form(
            reverse('intake-write_letter'), **declaration_answers)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.wsgi_request.path,
                         reverse('intake-write_letter'))

        self.assertTrue(result.context_data['form'].errors)

        event = models.ApplicationEvent.objects.filter(
            applicant_id=self.client.session['applicant_id'],
            name=models.ApplicationEvent.APPLICATION_ERRORS).first()

        self.assertDictEqual(
            result.context_data['form'].get_serialized_errors(),
            event.data['errors'])

    def test_no_existing_data(self):
        self.be_anonymous()
        with self.assertLogs(
                'intake.views.application_form_views', level=logging.WARN):
            result = self.client.get(reverse('intake-write_letter'))
            self.assertRedirects(result, reverse('intake-apply'))


class TestDeclarationLetterReviewPage(AuthIntegrationTestCase):

    fixtures = ['counties', 'organizations', 'mock_profiles']

    def test_get_with_expected_data(self):
        self.be_anonymous()
        mock_letter = mock.fake.declaration_letter_answers()
        mock_answers = mock.fake.alameda_pubdef_answers(
            first_name="foo", last_name="bar")
        counties = {'counties': constants.Counties.ALAMEDA}
        session_data = {**counties, **mock_answers, **mock_letter}
        self.set_session(
            form_in_progress={**counties, **mock_answers, **mock_letter})
        response = self.client.get(reverse('intake-review_letter'))
        self.assertContains(response, 'To Whom It May Concern')
        for portion in mock_letter.values():
            self.assertContains(response, html_utils.escape(portion))
        self.assertContains(response, 'Sincerely,')
        self.assertContains(response, 'Foo')
        self.assertContains(response, 'Bar')
        self.assertContains(
            response, 'name="submit_action" value="approve_letter"')
        self.assertContains(
            response, 'name="submit_action" value="edit_letter"')

    def test_get_with_no_existing_data(self):
        self.be_anonymous()
        with self.assertLogs(
                'intake.views.application_form_views', level=logging.WARN):
            result = self.client.get(reverse('intake-review_letter'))
            self.assertRedirects(result, reverse('intake-apply'))

    def test_post_edit_letter(self):
        self.be_anonymous()
        mock_letter = mock.fake.declaration_letter_answers()
        mock_answers = mock.fake.alameda_pubdef_answers()
        counties = {'counties': constants.Counties.ALAMEDA}
        self.set_session(
            form_in_progress={**counties, **mock_answers, **mock_letter},
            applicant_id=2)
        response = self.client.fill_form(
            reverse('intake-review_letter'),
            submit_action="edit_letter")
        self.assertRedirects(response, reverse('intake-write_letter'))
        applicant_id = self.client.session.get('applicant_id')
        self.assertTrue(applicant_id)
        self.assertEqual(models.FormSubmission.objects.filter(
            applicant_id=applicant_id).count(), 0)

    @patch(
        'intake.views.application_form_views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.session_view_base.notifications.slack_new_submission.send')
    def test_post_approve_letter(self, slack, send_confirmation):
        self.be_anonymous()
        applicant = models.Applicant()
        applicant.save()
        alameda = constants.Counties.ALAMEDA
        mock_letter = mock.fake.declaration_letter_answers()
        mock_answers = mock.fake.alameda_pubdef_answers()
        counties = {'counties': [alameda]}
        self.set_session(
            form_in_progress={**counties, **mock_answers, **mock_letter},
            applicant_id=applicant.id)
        response = self.client.fill_form(
            reverse('intake-review_letter'),
            submit_action="approve_letter")
        self.assertRedirects(response, reverse('intake-thanks'))

        applicant_id = self.client.session.get('applicant_id')
        self.assertTrue(applicant_id)

        submissions = list(models.FormSubmission.objects.filter(
            applicant_id=applicant_id))
        self.assertEqual(len(submissions), 1)
        submission = submissions[0]
        county_slugs = [county.slug for county in submission.get_counties()]
        self.assertListEqual(county_slugs, [alameda])
        self.assertIn(self.a_pubdef, submission.organizations.all())
        self.assertEqual(submission.organizations.count(), 1)
        self.assertEqual(submission.organizations.first().county.slug, alameda)
        filled_pdf_count = models.FilledPDF.objects.count()
        self.assertEqual(filled_pdf_count, 0)
        self.be_apubdef_user()
        resp = self.client.get(reverse("intake-app_index"))
        url = reverse(
            "intake-app_detail",
            kwargs={'submission_id': submission.id})
        self.assertContains(resp, url)
        self.assertTrue(slack.called)
        self.assertTrue(send_confirmation.called)


class TestThanks(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations',
        'mock_profiles',
        'mock_2_submissions_to_cc_pubdef']

    def test_anonymous_with_no_application_redirected_to_home(self):
        self.be_anonymous()
        response = self.client.get(reverse('intake-thanks'))
        self.assertRedirects(
            response, reverse('intake-home'), fetch_redirect_response=False)

    def test_existing_application_has_org_data(self):
        self.be_anonymous()
        app = models.Applicant()
        app.save()
        sub = models.FormSubmission.objects.all().first()
        sub.applicant_id = app.id
        sub.save()
        self.set_session(applicant_id=app.id)
        response = self.client.get(reverse('intake-thanks'))
        for org in sub.organizations.all():
            self.assertContains(response, html_utils.escape(org.name))
