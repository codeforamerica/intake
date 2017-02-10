from intake.tests.base_testcases import IntakeDataTestCase
from django.core.urlresolvers import reverse
from markupsafe import escape
from intake import models, services, utils
from intake.views.app_detail_views import NOT_ALLOWED_MESSAGE


class StatusUpdateViewBaseTestCase(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs', 'template_options'
        ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sub = cls.a_pubdef_submissions[0]
        cls.status_type = models.StatusType.objects.get(slug="eligible")
        cls.next_steps = [models.NextStep.objects.get(
            slug="wait-for-court-date")]

    def get_create_page(self):
        return self.client.get(reverse(
            'intake-create_status_update',
            kwargs=dict(submission_id=self.sub.id)))

    def create_status_update(self, user=None, **status_update_form_inputs):
        if 'author' not in status_update_form_inputs:
            status_update_form_inputs.update(author=self.a_pubdef_user.id)
        post_data = dict(
            status_type=self.status_type.id,
            next_steps=[step.id for step in self.next_steps],
            application=self.sub.applications.first().id,
            additional_information="you might be warned",
            other_next_step="nevertheless, persist"
        )
        post_data.update(**status_update_form_inputs)
        return self.client.fill_form(
            reverse(
                'intake-create_status_update',
                kwargs=dict(submission_id=self.sub.id)),
            **post_data)

    def get_review_page(self):
        return self.client.get(reverse(
                'intake-review_status_notification',
                kwargs=dict(submission_id=self.sub.id)))

    def confirm_status_update(self, **status_notification_form_inputs):
        return self.client.fill_form(
            reverse(
                'intake-review_status_notification',
                kwargs=dict(submission_id=self.sub.id)),
            **status_notification_form_inputs)


class TestStatusUpdateWorkflow(StatusUpdateViewBaseTestCase):
    # test case for multi-page workflow integration tests

    def test_return_from_review_page_displays_existing_form_data(self):
        self.be_apubdef_user()
        self.create_status_update(follow=True)
        response = self.get_create_page()
        self.assertContains(response, escape("nevertheless, persist"))

    def test_submitting_status_update_clears_session_for_new_one(self):
        self.be_apubdef_user()
        review_page = self.create_status_update(follow=True)
        default_message = \
            review_page.context_data['form']['sent_message'].value()
        self.confirm_status_update(sent_message=default_message, follow=True)
        create_page = self.get_create_page()
        self.assertNotContains(create_page, escape("nevertheless, persist"))
        session_key = \
            create_page.context_data['view'].get_session_storage_key()
        form_data = utils.get_form_data_from_session(
            create_page.wsgi_request, session_key)
        self.assertFalse(form_data)

    def test_user_sees_success_flash_and_new_status_after_submission(self):
        self.be_apubdef_user()
        review_page = self.create_status_update(follow=True)
        default_message = \
            review_page.context_data['form']['sent_message'].value()
        response = self.confirm_status_update(sent_message=default_message)
        self.assertRedirects(
            response, reverse('intake-app_index'),
            fetch_redirect_response=False)
        index = self.client.get(response.url)
        expected_message = services.status_notifications \
            .get_status_update_success_message(self.sub, self.status_type)
        self.assertContains(
            index, escape(expected_message))


class TestCreateStatusUpdateFormView(StatusUpdateViewBaseTestCase):

    def test_anon_redirected_to_login(self):
        self.be_anonymous()
        self.assertIn(
            reverse('user_accounts-login'), self.get_create_page().url)

    def test_incorrect_org_user_redirected_to_app_index(self):
        self.be_ccpubdef_user()
        response = self.get_create_page()
        self.assertRedirects(
            response, reverse('intake-app_index'),
            fetch_redirect_response=False)
        index = self.client.get(response.url)
        self.assertContains(index, escape(NOT_ALLOWED_MESSAGE))

    def test_cfa_user_redirected_to_app_index(self):
        self.be_cfa_user()
        response = self.get_create_page()
        self.assertRedirects(
            response, reverse('intake-app_index'),
            fetch_redirect_response=False)
        index = self.client.get(response.url)
        self.assertContains(index, escape(NOT_ALLOWED_MESSAGE))

    def test_submit_redirects_to_review_page(self):
        self.be_apubdef_user()
        response = self.create_status_update()
        self.assertRedirects(
            response,
            reverse(
                'intake-review_status_notification',
                kwargs=dict(submission_id=self.sub.id)),
            fetch_redirect_response=False)


class TestReviewStatusNotificationFormView(StatusUpdateViewBaseTestCase):

    def test_anon_redirected_to_login(self):
        self.be_anonymous()
        response = self.get_review_page()
        self.assertIn(
            reverse('user_accounts-login'), response.url)

    def test_incorrect_org_user_redirected_to_app_index(self):
        self.be_ccpubdef_user()
        response = self.get_review_page()
        self.assertRedirects(
            response, reverse('intake-app_index'),
            fetch_redirect_response=False)
        index = self.client.get(response.url)
        self.assertContains(index, escape(NOT_ALLOWED_MESSAGE))

    def test_cfa_user_redirected_to_app_index(self):
        self.be_cfa_user()
        response = self.get_review_page()
        self.assertRedirects(
            response, reverse('intake-app_index'),
            fetch_redirect_response=False)
        index = self.client.get(response.url)
        self.assertContains(index, escape(NOT_ALLOWED_MESSAGE))

    def test_correctly_renders_message(self):
        self.be_apubdef_user()
        response = self.create_status_update(follow=True)
        status_update_data = response.context_data['status_update']
        expected_message = services.status_notifications\
            .get_base_message_from_status_update_data(status_update_data)
        self.assertContains(response, escape(expected_message))

    def test_displays_correct_note_if_no_contact_prefs(self):
        self.be_apubdef_user()
        self.sub.answers['contact_preferences'] = []
        self.sub.save()
        self.create_status_update(follow=True)
        raise NotImplementedError

    def test_displays_correct_note_if_no_usable_contact_prefs(self):
        self.be_apubdef_user()
        self.sub.answers['contact_preferences'] = ['prefers_voicemail']

    def test_user_can_edit_message(self):
        self.be_apubdef_user()
        self.create_status_update(follow=True)
        edited_message = "Hi, I've been edited"
        response = self.confirm_status_update(
            sent_message=edited_message)
        self.assertRedirects(response, reverse('intake-app_index'))
        application = self.sub.applications.filter(
            organization=self.a_pubdef).first()
        status_update = application.status_updates.latest('updated')
        self.assertEqual(
            status_update.notification.sent_message, edited_message)
