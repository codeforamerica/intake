# These contain production data that impacts logic
# no dependencies (besides DB migration)
ESSENTIAL_DATA_FIXTURES = (
    'counties',
    'organizations',
    'addresses',
    'groups',
    'template_options',
)

# These contain fake accounts for each org
# depends on ESSENTIAL_DATA_FIXTURES
MOCK_USER_ACCOUNT_FIXTURES = (
    'mock_profiles',
)

# These are form submissions & fake applicant data
# depends on ESSENTIAL_DATA_FIXTURES
MOCK_APPLICATION_FIXTURES = (
    'mock_2_submissions_to_a_pubdef',
    'mock_2_submissions_to_ebclc',
    'mock_2_submissions_to_cc_pubdef',
    'mock_2_submissions_to_sf_pubdef',
    'mock_2_submissions_to_monterey_pubdef',
    'mock_2_submissions_to_solano_pubdef',
    'mock_2_submissions_to_san_diego_pubdef',
    'mock_2_submissions_to_san_joaquin_pubdef',
    'mock_2_submissions_to_santa_clara_pubdef',
    'mock_2_submissions_to_santa_cruz_pubdef',
    'mock_2_submissions_to_fresno_pubdef',
    'mock_2_submissions_to_sonoma_pubdef',
    'mock_2_submissions_to_tulare_pubdef',
    'mock_2_submissions_to_ventura_pubdef',
    'mock_2_submissions_to_santa_barbara_pubdef',
    'mock_2_submissions_to_yolo_pubdef',
    'mock_2_submissions_to_stanislaus_pubdef',
    'mock_1_submission_to_multiple_orgs',
)

MOCK_TRANSFER_FIXTURES = (
    'mock_2_transfers',
)

# These are fake case events (submitted, opened, processed, etc.)
# depends on MOCK_APPLICATION_FIXTURES and MOCK_USER_ACCOUNT_FIXTURES
MOCK_EVENT_FIXTURES = (
    'mock_application_events',
)

# These are fake bundles of applications
# depends on MOCK_APPLICATION_FIXTURES
MOCK_BUNDLE_FIXTURES = (
    'mock_1_bundle_to_a_pubdef',
    'mock_1_bundle_to_ebclc',
    'mock_1_bundle_to_sf_pubdef',
    'mock_1_bundle_to_cc_pubdef',
    'mock_1_bundle_to_monterey_pubdef',
    'mock_1_bundle_to_solano_pubdef',
    'mock_1_bundle_to_san_diego_pubdef',
    'mock_1_bundle_to_san_joaquin_pubdef',
    'mock_1_bundle_to_santa_clara_pubdef',
    'mock_1_bundle_to_santa_cruz_pubdef',
    'mock_1_bundle_to_fresno_pubdef',
    'mock_1_bundle_to_sonoma_pubdef',
    'mock_1_bundle_to_tulare_pubdef',
    'mock_1_bundle_to_ventura_pubdef',
    'mock_1_bundle_to_santa_barbara_pubdef',
    'mock_1_bundle_to_yolo_pubdef',
    'mock_1_bundle_to_stanislaus_pubdef',
)

# These all the fake mocked data
# depends on ESSENTIAL_DATA_FIXTURES
ALL_MOCK_DATA_FIXTURES = (
    MOCK_USER_ACCOUNT_FIXTURES +
    MOCK_APPLICATION_FIXTURES +
    MOCK_TRANSFER_FIXTURES +
    MOCK_BUNDLE_FIXTURES +
    MOCK_EVENT_FIXTURES
)
