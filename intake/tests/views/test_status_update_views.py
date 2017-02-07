from intake.tests.base_testcases import IntakeDataTestCase


class StatusUpdateViewBaseTestCase(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs', 'template_options'
        ]


class TestStatusUpdateWorkflow(StatusUpdateViewBaseTestCase):
    # test case for multi-page workflow integration tests

    def test_return_from_review_page_displays_existing_form_data(self):
        raise NotImplementedError

    def test_submitting_status_update_clears_session_for_new_one(self):
        raise NotImplementedError

    def test_user_sees_success_flash_and_new_status_after_submission(self):
        raise NotImplementedError


class TestCreateStatusUpdateFormView(StatusUpdateViewBaseTestCase):

    def test_access_permissions(self):
        raise NotImplementedError

    def test_submit_redirects_to_review_page(self):
        raise NotImplementedError

    def test_displays_note_if_no_contact_info(self):
        raise NotImplementedError


class TestReviewStatusNotificationFormView(StatusUpdateViewBaseTestCase):

    def test_access_permissions(self):
        raise NotImplementedError

    def test_submit_redirects_to_app_index(self):
        raise NotImplementedError

    def test_correctly_renders_message(self):
        raise NotImplementedError

    def test_displays_note_if_no_contact_info(self):
        raise NotImplementedError

    def test_user_can_edit_message(self):
        raise NotImplementedError
