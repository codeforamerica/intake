import os
import random
import logging
from unittest import skipUnless
from unittest.mock import patch
from django.test import TestCase
from user_accounts.tests.test_auth_integration import AuthIntegrationTestCase
from django.db.models import Count
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import html as html_utils

from intake.tests import mock
from intake import models, views, constants
from user_accounts import models as auth_models
from formation import fields, forms

from project.jinja2 import url_with_ids

DELUXE_TEST = os.environ.get('DELUXE_TEST', False)


class IntakeDataTestCase(AuthIntegrationTestCase):

    display_field_checks = [
        'first_name',
        'last_name',
        'phone_number',
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


class TestViews(IntakeDataTestCase):

    fixtures = [
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
        'intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
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
        'intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
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
        self.assertContains(result, views.Confirm.incoming_message)
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

    def test_apply_with_insufficient_form(self):
        # should return the same page, with the partially filled form
        self.set_session_counties()
        result = self.client.fill_form(
            reverse('intake-county_application'),
            first_name="Foooo"
        )
        self.assertContains(result, "Foooo")
        self.assertEqual(
            result.wsgi_request.path,
            reverse('intake-county_application'))
        self.assertContains(result, "This field is required.")
        self.assertContains(
            result, fields.AddressField.is_recommended_error_message)
        self.assertContains(
            result,
            fields.SocialSecurityNumberField.is_recommended_error_message)
        self.assertContains(
            result, fields.DateOfBirthField.is_recommended_error_message)

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
    @patch('intake.models.notifications.slack_submissions_viewed.send')
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
    @patch('intake.models.notifications.slack_submissions_viewed.send')
    @patch('intake.models.notifications.slack_simple.send')
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
    def test_authenticated_user_can_see_pdf_bundle(self):
        self.be_sfpubdef_user()
        ids = models.FormSubmission.objects.filter(
            organizations=self.sf_pubdef).values_list('pk', flat=True)
        url = url_with_ids('intake-pdf_bundle', ids)
        bundle = self.client.get(url, follow=True)
        self.assertEqual(bundle.status_code, 200)

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
    def test_staff_user_can_see_pdf_bundle(self):
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

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_authenticated_user_can_see_app_bundle(self, slack):
        self.be_cfa_user()
        submissions = self.submissions
        ids = [s.id for s in submissions]
        url = url_with_ids('intake-app_bundle', ids)
        bundle = self.client.get(url)
        self.assertEqual(bundle.status_code, 200)

    @patch('intake.views.notifications.slack_submissions_deleted.send')
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

    @patch('intake.views.notifications.slack_submissions_processed.send')
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
    fixtures = ['organizations']

    def test_returns_200_with_org_name_list(self):
        response = self.client.get(reverse('intake-partner_list'))
        orgs = auth_models.Organization.objects.filter(
            is_receiving_agency=True)
        self.assertEqual(response.status_code, 200)
        for org in orgs:
            self.assertContains(response, org.name)


class TestPartnerDetailView(TestCase):
    fixtures = ['organizations']

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


class TestRAPSheetInstructions(TestCase):

    def test_renders_with_no_session_data(self):
        response = self.client.get(reverse('intake-rap_sheet'))
        # make sure it has a link to the pdf
        # make sure there aren't any unrendered variables
        self.assertNotContains(response, "{{")


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
        events = list(applicant.events.all())
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.name,
                         constants.ApplicationEventTypes.APPLICATION_STARTED)

        self.assertIn('ip', event.data)
        self.assertIn('user_agent', event.data)
        self.assertEqual(event.data['user_agent'], 'tester')
        self.assertIn('referrer', event.data)

    def test_anonymous_user_cannot_submit_empty_county_selection(self):
        self.be_anonymous()
        result = self.client.fill_form(
            reverse('intake-apply'))
        self.assertEqual(result.status_code, 200)
        form = result.context['form']
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)


class TestMultiCountyApplication(AuthIntegrationTestCase):

    fixtures = ['organizations']

    @patch(
        'intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
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
            name=constants.ApplicationEventTypes.APPLICATION_SUBMITTED).count()

        self.assertEqual(1, submitted_event_count)

    @patch(
        'intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
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
        self.assertTrue(result.context['form'].email.errors)
        self.assertTrue(result.context['form'].phone_number.errors)

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)
        self.assertRedirects(result, reverse('intake-thanks'))
        self.assertTrue(slack.called)
        self.assertTrue(send_confirmation.called)

    @patch(
        'intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
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
        'intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
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
        self.assertTrue(result.context['form'].errors)
        slack.assert_not_called()
        send_confirmation.assert_not_called()

    @patch(
        'intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
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
        'intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
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
        self.assertTrue(result.context['form'].errors)
        slack.assert_not_called()
        send_confirmation.assert_not_called()

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


class TestDeclarationLetterView(AuthIntegrationTestCase):

    fixtures = ['organizations', 'mock_profiles']

    @patch(
        'intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
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
        'intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
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

        self.assertTrue(result.context['form'].errors)

    def test_no_existing_data(self):
        self.be_anonymous()
        with self.assertLogs('intake.views', level=logging.WARN):
            result = self.client.get(reverse('intake-write_letter'))
            self.assertRedirects(result, reverse('intake-apply'))


class TestDeclarationLetterReviewPage(AuthIntegrationTestCase):

    fixtures = ['organizations', 'mock_profiles']

    def test_get_with_expected_data(self):
        self.be_anonymous()
        mock_letter = mock.fake.declaration_letter_answers()
        mock_answers = mock.fake.alameda_pubdef_answers(
            first_name="foo", last_name="bar")
        counties = {'counties': constants.Counties.ALAMEDA}
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
        with self.assertLogs('intake.views', level=logging.WARN):
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
        'intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
    def test_post_approve_letter(self, slack, send_confirmation):
        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        mock_letter = mock.fake.declaration_letter_answers()
        mock_answers = mock.fake.alameda_pubdef_answers()
        counties = {'counties': [alameda]}
        self.set_session(
            form_in_progress={**counties, **mock_answers, **mock_letter},
            applicant_id=2)
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



class TestApplicationDetail(IntakeDataTestCase):

    fixtures = [
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_alameda_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs'
        ]

    def get_detail(self, submission):
        result = self.client.get(
            reverse('intake-app_detail',
                    kwargs=dict(submission_id=submission.id)))
        return result

    def assertHasDisplayData(self, response, submission):
        for field, value in submission.answers.items():
            if field in self.display_field_checks:
                escaped_value = html_utils.conditional_escape(value)
                self.assertContains(response, escaped_value)

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_logged_in_user_can_get_submission_display(self, slack):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        result = self.get_detail(submission)
        self.assertEqual(result.context['submission'], submission)
        self.assertHasDisplayData(result, submission)

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_staff_user_can_get_submission_display(self, slack):
        self.be_cfa_user()
        submission = self.a_pubdef_submissions[0]
        result = self.get_detail(submission)
        self.assertEqual(result.context['submission'], submission)
        self.assertHasDisplayData(result, submission)

    @patch('intake.models.FillablePDF')
    @patch('intake.models.notifications.slack_submissions_viewed.send')
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

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_user_cant_see_app_detail_for_other_county(self, slack):
        self.be_ccpubdef_user()
        submission = self.sf_pubdef_submissions[0]
        response = self.get_detail(submission)
        self.assertRedirects(response, reverse('intake-app_index'))
        slack.assert_not_called()

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_user_can_see_app_detail_for_multi_county(self, slack):
        self.be_apubdef_user()
        submission = self.combo_submissions[0]
        response = self.get_detail(submission)
        self.assertHasDisplayData(response, submission)

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_agency_user_can_see_transfer_action_link(self, slack):
        self.be_apubdef_user()
        submission = self.a_pubdef_submissions[0]
        response = self.get_detail(submission)
        transfer_action_url = html_utils.conditional_escape(
            submission.get_transfer_action(response.wsgi_request)['url'])
        self.assertContains(response, transfer_action_url)


class TestApplicationBundle(IntakeDataTestCase):

    fixtures = [
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_alameda_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs',
        'mock_1_bundle_to_sf_pubdef',
        'mock_1_bundle_to_alameda_pubdef',
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

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_user_can_get_app_bundle_without_pdf(self, slack):
        self.be_apubdef_user()
        response = self.get_submissions(self.a_pubdef_submissions)
        self.assertNotContains(response, 'iframe class="pdf_inset"')
        self.assertHasDisplayData(response, self.a_pubdef_submissions)

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_staff_user_can_get_app_bundle_with_pdf(self, slack):
        self.be_cfa_user()
        response = self.get_submissions(self.combo_submissions)
        self.assertContains(response, 'iframe class="pdf_inset"')
        self.assertHasDisplayData(response, self.combo_submissions)

    @skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_user_can_get_bundle_with_pdf(self, slack):
        self.be_sfpubdef_user()
        response = self.get_submissions(self.sf_pubdef_submissions)
        self.assertContains(response, 'iframe class="pdf_inset"')

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_user_cant_see_app_bundle_for_other_county(self, slack):
        self.be_sfpubdef_user()
        response = self.get_submissions(self.a_pubdef_submissions)
        self.assertEqual(response.status_code, 404)
        slack.assert_not_called()

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_user_can_see_app_bundle_for_multi_county(self, slack):
        self.be_apubdef_user()
        response = self.get_submissions(self.combo_submissions)
        self.assertNotContains(response, 'iframe class="pdf_inset"')
        self.assertHasDisplayData(response, self.combo_submissions)


class TestApplicationIndex(IntakeDataTestCase):

    fixtures = [
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_alameda_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs',
        'mock_1_bundle_to_sf_pubdef',
        'mock_1_bundle_to_alameda_pubdef',
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

    def test_pdf_users_see_pdf_link(self):
        self.be_sfpubdef_user()
        # look for the pdf link of each app
        response = self.client.get(reverse('intake-app_index'))
        self.assertEqual(response.context['show_pdf'], True)
        for sub in self.sf_pubdef_submissions:
            pdf_url = reverse('intake-filled_pdf', kwargs=dict(
                submission_id=sub.id))
            self.assertContains(response, pdf_url)

    def test_non_pdf_users_dont_see_pdf_link(self):
        self.be_apubdef_user()
        # look for the pdf link of each app
        response = self.client.get(reverse('intake-app_index'))
        self.assertEqual(response.context['show_pdf'], False)
        for sub in self.combo_submissions:
            pdf_url = reverse('intake-filled_pdf', kwargs=dict(
                submission_id=sub.id))
            self.assertNotContains(response, pdf_url)

    def test_cfa_users_see_pdf_link(self):
        self.be_cfa_user()
        # look for the pdf link of each app
        response = self.client.get(reverse('intake-app_index'))
        self.assertEqual(response.context['show_pdf'], True)
        for sub in self.sf_pubdef_submissions:
            pdf_url = reverse('intake-filled_pdf', kwargs=dict(
                submission_id=sub.id))
            self.assertContains(response, pdf_url)


class TestStats(IntakeDataTestCase):

    fixtures = [
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_alameda_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_2_submissions_to_cc_pubdef',
        'mock_1_submission_to_multiple_orgs',
        ]

    def test_that_page_shows_counts_by_county(self):
        # get numbers
        all_any = 7
        all_sf = 3
        all_cc = 3
        total = "{} total applications".format(all_any)
        sf_string = "{} applications for San Francisco County".format(all_sf)
        cc_string = "{} applications for Contra Costa County".format(all_cc)
        self.be_anonymous()
        response = self.client.get(reverse('intake-stats'))
        for search_term in [total, sf_string, cc_string]:
            self.assertContains(response, search_term)


class TestDailyTotals(TestCase):

    fixtures = [
        'organizations',
        'mock_2_submissions_to_alameda_pubdef']

    def test_returns_200(self):
        response = self.client.get(reverse('intake-daily_totals'))
        self.assertEqual(response.status_code, 200)


class TestApplicationBundleDetail(IntakeDataTestCase):

    fixtures = [
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_alameda_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs',
        'mock_1_bundle_to_alameda_pubdef',
    ]

    @patch('intake.views.notifications.slack_submissions_viewed.send')
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

    @patch('intake.views.notifications.slack_submissions_viewed.send')
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
        self.assertRedirects(result, reverse('intake-app_index'))

    @patch('intake.views.notifications.slack_submissions_viewed.send')
    def test_has_pdf_bundle_url_if_needed(self, slack):
        """ApplicationBundleDetailView return pdf url if needed

        create an `ApplicationBundle` that needs a pdf
        try to access `ApplicationBundleDetailView` using `id`
        assert that the url for `FilledPDFBundle` is in the template.
        """
        self.be_sfpubdef_user()
        mock_pdf = SimpleUploadedFile(
            'a.pdf', b"things", content_type="application/pdf")
        bundle = models.ApplicationBundle.create_with_submissions(
            organization=self.sf_pubdef,
            submissions=self.sf_pubdef_submissions,
            bundled_pdf=mock_pdf
            )
        url = bundle.get_pdf_bundle_url()
        result = self.client.get(reverse(
                    'intake-app_bundle_detail',
                    kwargs=dict(bundle_id=bundle.id)))
        self.assertContains(result, url)

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_agency_user_can_see_transfer_action_links(self, slack):
        self.be_apubdef_user()
        response = self.client.get(
            self.a_pubdef_bundle.get_absolute_url())
        for sub in self.a_pubdef_submissions:
            transfer_action_url = html_utils.conditional_escape(
                sub.get_transfer_action(response.wsgi_request)['url'])
            self.assertContains(response, transfer_action_url)


@skipUnless(DELUXE_TEST, "Super slow, set `DELUXE_TEST=1` to run")
class TestApplicationBundleDetailPDFView(IntakeDataTestCase):
    fixtures = [
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_sf_pubdef',
        ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.bundle = models.ApplicationBundle.create_with_submissions(
            organization=cls.sf_pubdef, submissions=cls.sf_pubdef_submissions)

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
        bundle = models.ApplicationBundle.create_with_submissions(
                    organization=self.sf_pubdef,
                    submissions=self.sf_pubdef_submissions,
                    skip_pdf=True)
        response = self.client.get(bundle.get_pdf_bundle_url())
        self.assertEqual(response.status_code, 404)


class TestReferToAnotherOrgView(IntakeDataTestCase):

    fixtures = [
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_alameda_pubdef',
        'mock_1_bundle_to_alameda_pubdef']
    mock_sub_id = 485
    mock_bundle_id = 14

    def url(self, org_id, sub_id=485, next=None):
        base = reverse(
            'intake-mark_transferred_to_other_org')
        base += "?ids={sub_id}&to_organization_id={org_id}".format(
            sub_id=sub_id, org_id=org_id)
        if next:
            base += "&next={}".format(next)
        return base

    @patch('intake.views.notifications.slack_submission_transferred.send')
    def test_anon_is_rejected(self, slack_action):
        self.be_anonymous()
        response = self.client.get(self.url(
            1))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_accounts-login'), response.url)
        slack_action.assert_not_called()

    @patch('intake.views.notifications.slack_submission_transferred')
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

    @patch('intake.views.notifications.slack_submissions_viewed.send')
    @patch('intake.views.notifications.slack_submission_transferred')
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
