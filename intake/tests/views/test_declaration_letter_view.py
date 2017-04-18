from django.test import TestCase


class TestWriteDeclarationLetterView(TestCase):

    def test_renders_declaration_letter_form(self):
        pass

    def test_with_no_applicant(self):
        pass

    def test_applicant_with_no_counties(self):
        pass

    def test_get_displays_existing_answers(self):
        pass

    def test_post_redirects_to_letter_review_page(self):
        pass

    def test_invalid_post_shows_errors(self):
        pass

    def test_shows_counties_where_applying(self):
        pass

    def test_logs_page_complete_event(self):
        pass

    def test_saves_form_data_to_session(self):
        pass

    def test_logs_validation_errors_event(self):
        pass

    def test_shows_error_messages_in_flash(self):
        pass


class TestReviewDeclarationLetterView(TestCase):

    def test_shows_counties_where_applying(self):
        pass

    def test_with_no_applicant(self):
        pass

    def test_applicant_with_no_counties(self):
        pass

    def test_displays_existing_form_answers(self):
        pass

    def test_approve_redirects_to_thanks_page(self):
        pass

    def test_edit_redirects_to_write_letter_page(self):
        pass

    def test_invalid_post_returns_same_page(self):
        pass

    def test_logs_page_complete_event(self):
        pass

    def test_saves_form_data_to_session(self):
        pass

    def test_logs_validation_errors_event(self):
        pass

    def test_shows_error_messages_in_flash(self):
        pass
