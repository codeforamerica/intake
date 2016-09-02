from unittest.mock import patch
import random
from user_accounts.tests.test_auth_integration import AuthIntegrationTestCase
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import html as html_utils

from intake.tests import mock
from intake import models, views, constants
from user_accounts import models as auth_models
from formation import fields, forms

from project.jinja2 import url_with_ids


class IntakeDataTestCase(AuthIntegrationTestCase):

    display_field_checks = [
        'first_name',
        'last_name',
        'phone_number',
        'email',
        'monthly_expenses'
    ]

    fixtures = ['organizations']

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.have_some_submissions()
        cls.have_a_fillable_pdf()

    @classmethod
    def have_some_submissions(cls):
        organizations = auth_models.Organization.objects.all()
        for org in organizations:
            setattr(cls, org.slug, org)
        counties = models.County.objects.all()
        for county in counties:
            if county.slug == constants.Counties.SAN_FRANCISCO:
                cls.sfcounty = county
            elif county.slug == constants.Counties.CONTRA_COSTA:
                cls.cccounty = county
        cls.sf_submissions = list(
            mock.FormSubmissionFactory.create_batch(
                2, organizations=[cls.sf_pubdef]))
        cls.cc_submissions = list(
            mock.FormSubmissionFactory.create_batch(
                2, organizations=[cls.cc_pubdef]))
        cls.combo_submissions = list(
            mock.FormSubmissionFactory.create_batch(
                2, organizations=[cls.sf_pubdef, cls.cc_pubdef]))
        cls.submissions = [
            *cls.sf_submissions,
            *cls.cc_submissions,
            *cls.combo_submissions]

    @classmethod
    def have_a_fillable_pdf(cls):
        cls.fillable = mock.fillable_pdf(organization=cls.sfpubdef)

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


    def setUp(self):
        super().setUp()
        self.session = self.client.session

    def set_session_counties(self, counties=None):
        if not counties:
            counties = [constants.Counties.SAN_FRANCISCO]
        self.session['form_in_progress'] = {
            'counties': counties}
        self.session.save()

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
        base_data = mock.post_data(
            counties=['sanfrancisco'],
            **mock.NEW_RAW_FORM_DATA)
        session = self.client.session
        session['form_in_progress'] = dict(base_data.lists())
        session.save()
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

    @patch('intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
    def test_anonymous_user_can_fill_out_app_and_reach_thanks_page(
            self, slack, send_confirmation):
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
        organization = submission.counties.first().organizations.first()
        self.assertEqual(filled_pdf.original_pdf, organization.pdfs.first())
        self.assertContains(thanks_page, "Thank")
        self.assert_called_once_with_types(
            slack,
            submission='FormSubmission',
            request='WSGIRequest',
            submission_count='int')
        send_confirmation.assert_called_once_with()

    @patch('intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
    def test_apply_with_name_only(self, slack, send_confirmation):
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
        self.assertRedirects(result, reverse('intake-confirm'))
        result = self.client.get(result.url)
        self.assertContains(result, "Foo")
        self.assertContains(result, "Bar")
        self.assertContains(
            result, fields.AddressField.is_recommended_error_message)
        self.assertContains(
            result, fields.SocialSecurityNumberField.is_recommended_error_message)
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

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_authenticated_user_can_see_filled_pdf(self, slack):
        self.be_sfpubdef_user()
        submission = self.submissions[0]

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
        self.assert_called_once_with_types(
            slack, submissions='list', user='User')

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    @patch('intake.models.notifications.slack_simple.send')
    def test_authenticated_user_can_get_filled_pdf_without_building(
            self, slack_simple, slack_viewed):
        """
        test_authenticated_user_can_get_filled_pdf_without_building

        this tests that a pdf will be served even if not pregenerated
        """
        self.be_sfpubdef_user()
        submission = self.submissions[0]

        filled_pdf_bytes = self.fillable.fill(submission)
        pdf_file = SimpleUploadedFile('filled.pdf', filled_pdf_bytes,
                                      content_type='application/pdf')
        pdf = self.client.get(reverse('intake-filled_pdf',
                                      kwargs=dict(
                                          submission_id=submission.id
                                      )))
        self.assertEqual(type(pdf.content), bytes)
        self.assert_called_once_with_types(
            slack_viewed, submissions='list', user='User')

    def test_authenticated_user_can_see_list_of_submitted_apps(self):
        self.be_cfa_user()
        index = self.client.get(reverse('intake-app_index'))
        for submission in self.submissions:
            self.assertContains(
                index,
                html_utils.escape(submission.answers['last_name'])
            )

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
        self.be_sfpubdef_user()
        ids = [s.id for s in self.submissions]
        url = url_with_ids('intake-pdf_bundle', ids)
        bundle = self.client.get(url)
        self.assertEqual(bundle.status_code, 200)

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_authenticated_user_can_see_app_bundle(self, slack):
        self.be_cfa_user()
        # we need a pdf for this users organization
        ids = [s.id for s in self.submissions]
        url = url_with_ids('intake-app_bundle', ids)
        bundle = self.client.get(url)
        self.assertEqual(bundle.status_code, 200)
        self.assert_called_once_with_types(
            slack,
            submissions='list',
            user='User')

    @patch('intake.views.notifications.slack_submissions_deleted.send')
    def test_authenticated_user_can_delete_apps(self, slack):
        self.be_cfa_user()
        submission = self.submissions[-1]
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
        self.assert_called_once_with_types(
            slack,
            submissions='list',
            user='User')

    @patch('intake.views.MarkProcessed.notification_function')
    def test_agency_user_can_mark_apps_as_processed(self, slack):
        self.be_sfpubdef_user()
        submissions = self.submissions[:2]
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
            self.assertRedirects(response, new,
                                 status_code=301, fetch_redirect_response=False)

        for old_template, new_view in id_redirects.items():
            old = old_template.format(old_uuids[2])
            response = self.client.get(old)
            new = reverse(
                new_view, kwargs=dict(
                    submission_id=ported_models[2].id))
            self.assertRedirects(response, new,
                                 status_code=301, fetch_redirect_response=False)

        for old_template, new_view in multi_id_redirects.items():
            old = old_template.format(key_params)
            response = self.client.get(old)
            new = url_with_ids(new_view, [s.id for s in ported_models_query])
            self.assertRedirects(response, new,
                                 status_code=301, fetch_redirect_response=False)


class TestSelectCountyView(AuthIntegrationTestCase):

    def test_anonymous_user_can_access_county_view(self):
        self.be_anonymous()
        county_view = self.client.get(
            reverse('intake-apply'))
        for slug, description in constants.COUNTY_CHOICES:
            self.assertContains(county_view, slug)
            self.assertContains(county_view, html_utils.escape(description))

    def test_anonymous_user_can_submit_county_selection(self):
        self.be_anonymous()
        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=['contracosta'])
        self.assertRedirects(result, reverse('intake-county_application'))


class TestMultiCountyApplication(AuthIntegrationTestCase):

    fixtures = ['organizations']

    @patch('intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
    def test_can_apply_to_contra_costa_alone(self, slack, send_confirmation):
        self.be_anonymous()
        contracosta = constants.Counties.CONTRA_COSTA
        cc_pubdef = constants.Organizations.COCO_PUBDEF
        answers = mock.fake.contra_costa_county_form_answers()

        county_fields = forms.ContraCostaForm.fields
        other_county_fields = \
            forms.SanFranciscoCountyForm.fields | forms.OtherCountyForm.fields
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
        form = result.context['form']
        self.assertListEqual(form.counties, [contracosta])

        for field_name in county_specific_field_names:
            self.assertContains(result, field_name)

        for field_name in other_county_field_names:
            self.assertNotContains(result, field_name)

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)
        self.assertRedirects(result, reverse('intake-thanks'))
        lookup = {
            key: answers[key]
            for key in [
                'email', 'phone_number', 'monthly_expenses']}

        submission = models.FormSubmission.objects.filter(
            answers__contains=lookup).first()
        county_slugs = [county.slug for county in submission.counties.all()]
        self.assertListEqual(county_slugs, [contracosta])
        org_slugs = [org.slug for org in submission.organizations.all()]
        self.assertListEqual(org_slugs, [cc_pubdef])

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
        required_fields = forms.ContraCostaForm.required_fields

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

    @patch(
        'intake.views.models.FormSubmission.send_confirmation_notifications')
    @patch('intake.views.notifications.slack_new_submission.send')
    def test_can_apply_to_alameda_alone(self, slack, send_confirmation):
        self.be_anonymous()
        alameda = constants.Counties.ALAMEDA
        answers = mock.fake.alameda_county_form_answers()
        result = self.client.fill_form(
            reverse('intake-apply'), counties=[alameda])
        self.assertRedirects(result, reverse('intake-county_application'))
        result = self.client.get(reverse('intake-county_application'))
        form = result.context['form']
        self.assertListEqual(form.counties, [alameda])

        result = self.client.fill_form(
            reverse('intake-county_application'),
            **answers)
        lookup = {
            key: answers[key]
            for key in [
                'email', 'phone_number', 'first_name']}

        submission = models.FormSubmission.objects.filter(
            answers__contains=lookup).first()
        county_slugs = [county.slug for county in submission.counties.all()]
        self.assertListEqual(county_slugs, [alameda])
        self.assertEqual(submission.organizations.count(), 1)
        self.assertEqual(submission.organizations.first().county.slug, alameda)
        filled_pdf_count = models.FilledPDF.objects.count()
        self.assertEqual(filled_pdf_count, 0)

    def test_can_go_back_and_reset_counties(self):
        self.be_anonymous()
        county_slugs = [slug for slug, text in constants.COUNTY_CHOICES]
        first_choices = random.sample(county_slugs, 2)
        second_choices = [random.choice(county_slugs)]
        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=first_choices,
            follow=True)
        form = result.context['form']
        self.assertEqual(form.counties, first_choices)
        county_setting = self.client.session['form_in_progress']['counties']
        self.assertEqual(county_setting, first_choices)

        result = self.client.fill_form(
            reverse('intake-apply'),
            counties=second_choices,
            follow=True)
        form = result.context['form']
        self.assertEqual(form.counties, second_choices)
        county_setting = self.client.session['form_in_progress']['counties']
        self.assertEqual(county_setting, second_choices)


class TestApplicationDetail(IntakeDataTestCase):

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
        user = self.be_ccpubdef_user()
        submission = self.cc_submissions[0]
        result = self.get_detail(submission)
        self.assertEqual(result.context['submission'], submission)
        self.assert_called_once_with_types(
            slack, submissions='list', user='User')
        self.assertHasDisplayData(result, submission)

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_staff_user_can_get_submission_display(self, slack):
        user = self.be_cfa_user()
        submission = self.combo_submissions[0]
        result = self.get_detail(submission)
        self.assertEqual(result.context['submission'], submission)
        self.assert_called_once_with_types(
            slack, submissions='list', user='User')
        self.assertHasDisplayData(result, submission)

    @patch('intake.models.FillablePDF')
    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_user_with_pdf_redirected_to_pdf(self, slack, FillablePDF):
        self.be_sfpubdef_user()
        submission = self.sf_submissions[0]
        result = self.get_detail(submission)
        self.assertRedirects(result, reverse('intake-filled_pdf',
                                             kwargs=dict(submission_id=submission.id)),
                             fetch_redirect_response=False)
        slack.assert_not_called()  # notification should be deferred to pdf view
        FillablePDF.assert_not_called()

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_user_cant_see_app_detail_for_other_county(self, slack):
        self.be_ccpubdef_user()
        submission = self.sf_submissions[0]
        response = self.get_detail(submission)
        self.assertRedirects(response, reverse('intake-app_index'))
        slack.assert_not_called()

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_user_can_see_app_detail_for_multi_county(self, slack):
        self.be_ccpubdef_user()
        submission = self.combo_submissions[0]
        response = self.get_detail(submission)
        self.assert_called_once_with_types(
            slack, submissions='list', user='User')
        self.assertHasDisplayData(response, submission)


class TestApplicationBundle(IntakeDataTestCase):

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
        user = self.be_ccpubdef_user()
        response = self.get_submissions(self.cc_submissions)
        self.assert_called_once_with_types(
            slack, submissions='list', user='User')
        self.assertNotContains(response, 'iframe class="pdf_inset"')
        self.assertHasDisplayData(response, self.cc_submissions)

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_staff_user_can_get_app_bundle_without_pdf(self, slack):
        user = self.be_cfa_user()
        response = self.get_submissions(self.combo_submissions)
        self.assert_called_once_with_types(
            slack, submissions='list', user='User')
        self.assertNotContains(response, 'iframe class="pdf_inset"')
        self.assertHasDisplayData(response, self.combo_submissions)

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_user_can_get_bundle_with_pdf(self, slack):
        self.be_sfpubdef_user()
        response = self.get_submissions(self.sf_submissions)
        self.assertContains(response, 'iframe class="pdf_inset"')
        self.assert_called_once_with_types(
            slack, submissions='list', user='User')

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_user_cant_see_app_bundle_for_other_county(self, slack):
        self.be_sfpubdef_user()
        response = self.get_submissions(self.cc_submissions)
        self.assertRedirects(response, reverse('intake-app_index'))
        response = self.client.get(response.url)
        slack.assert_not_called()

    @patch('intake.models.notifications.slack_submissions_viewed.send')
    def test_user_can_see_app_bundle_for_multi_county(self, slack):
        self.be_ccpubdef_user()
        response = self.get_submissions(self.combo_submissions)
        self.assert_called_once_with_types(
            slack, submissions='list', user='User')
        self.assertNotContains(response, 'iframe class="pdf_inset"')
        self.assertHasDisplayData(response, self.combo_submissions)


class TestApplicationIndex(IntakeDataTestCase):

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
        self.be_ccpubdef_user()
        response = self.client.get(reverse('intake-app_index'))
        self.assertContainsSubmissions(response, self.cc_submissions)
        self.assertContainsSubmissions(response, self.combo_submissions)
        self.assertNotContainsSubmissions(response, self.sf_submissions)

    def test_that_cfa_user_can_see_apps_to_all_orgs(self):
        self.be_cfa_user()
        response = self.client.get(reverse('intake-app_index'))
        self.assertContainsSubmissions(response, self.cc_submissions)

    def test_org_user_sees_name_of_org_in_index(self):
        user = self.be_ccpubdef_user()
        response = self.client.get(reverse('intake-app_index'))
        self.assertContains(response, user.profile.organization.name)


class TestStats(IntakeDataTestCase):

    def test_that_page_shows_counts_by_county(self):
        # get numbers
        all_any = len(self.submissions)
        all_sf = len(self.sf_submissions) + len(self.combo_submissions)
        all_cc = len(self.cc_submissions) + len(self.combo_submissions)
        total = "{} total applications".format(all_any)
        sf_string = "{} applications for San Francisco County".format(all_sf)
        cc_string = "{} applications for Contra Costa County".format(all_cc)
        self.be_anonymous()
        response = self.client.get(reverse('intake-stats'))
        for search_term in [total, sf_string, cc_string]:
            self.assertContains(response, search_term)


class TestApplicationBundleDetailView(IntakeDataTestCase):

    @patch('intake.views.notifications.slack_submissions_viewed.send')
    def test_returns_200_on_existing_bundle_id(self, slack):
        """`ApplicationBundleDetailView` return `OK` for existing bundle

        create an `ApplicationBundle`,
        try to access `ApplicationBundleDetailView` using `id`
        assert that 200 OK is returned
        """
        self.be_ccpubdef_user()
        bundle = models.ApplicationBundle.create_with_submissions(
            organization=self.ccpubdef, submissions=self.submissions)
        result = self.client.get(reverse(
                    'intake-app_bundle_detail',
                    kwargs=dict(bundle_id=bundle.id)))
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
        bundle = models.ApplicationBundle.create_with_submissions(
            organization=self.ccpubdef, submissions=self.submissions)
        self.be_sfpubdef_user()
        result = self.client.get(reverse(
                    'intake-app_bundle_detail',
                    kwargs=dict(bundle_id=bundle.id)))
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
            organization=self.sfpubdef,
            submissions=self.submissions,
            bundled_pdf=mock_pdf
            )
        url = bundle.get_pdf_bundle_url()
        result = self.client.get(reverse(
                    'intake-app_bundle_detail',
                    kwargs=dict(bundle_id=bundle.id)))
        self.assertContains(result, url)
