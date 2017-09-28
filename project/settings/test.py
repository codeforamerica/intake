from unittest.mock import patch

mailgun_patcher = patch(
    'intake.services.contact_info_validation_service'
    '.validate_email_with_mailgun')
mailgun_patcher.start()
mailgun_patcher.return_value = (True, None)