from intake.tests.base_testcases import IntakeDataTestCase


class StatusUpdateViewBaseTestCase(IntakeDataTestCase):

    fixtures = [
        'counties',
        'organizations', 'mock_profiles',
        'mock_2_submissions_to_a_pubdef',
        'mock_2_submissions_to_sf_pubdef',
        'mock_1_submission_to_multiple_orgs', 'template_options'
        ]


class TestCreateStatusUpdateFormView(StatusUpdateViewBaseTestCase):
    pass


class TestReviewStatusNotificationFormView(StatusUpdateViewBaseTestCase):
    pass
