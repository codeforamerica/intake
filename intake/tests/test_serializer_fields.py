from intake import models
from django.test import TestCase

from intake.serializers.fields import made_a_meaningful_attempt_to_apply


def make_applicant():
    applicant = models.Applicant()
    applicant.save()
    return applicant


def make_county_form_completed_event(applicant):
    event = models.ApplicationEvent(
        applicant=applicant,
        name=models.ApplicationEvent.APPLICATION_PAGE_COMPLETE,
        data=dict(page_name='CountyApplication'))
    event.save()


def make_error_event(applicant, errors):
    event = models.ApplicationEvent(
        applicant=applicant,
        name=models.ApplicationEvent.APPLICATION_ERRORS,
        data=dict(errors=errors))
    event.save()


class TestMadeAMeaningfulAttemptToApply(TestCase):

    def test_completed_county_form_returns_true(self):
        applicant = make_applicant()
        make_county_form_completed_event(applicant)
        self.assertTrue(
            made_a_meaningful_attempt_to_apply(applicant))

    def test_errors_from_select_county_only_returns_false(self):
        applicant = make_applicant()
        make_error_event(applicant, dict(counties=['required']))
        self.assertFalse(
            made_a_meaningful_attempt_to_apply(applicant))

    def test_errors_from_empty_county_form_returns_false(self):
        applicant = make_applicant()
        make_error_event(applicant, dict(first_name=['required']))
        self.assertFalse(
            made_a_meaningful_attempt_to_apply(applicant))

    def test_errors_from_county_form_without_first_name_returns_true(self):
        applicant = make_applicant()
        make_error_event(applicant, dict(last_name=['required']))
        self.assertTrue(
            made_a_meaningful_attempt_to_apply(applicant))

    def test_empty_forms_with_later_genuine_attempt_returns_true(self):
        applicant = make_applicant()
        make_error_event(applicant, dict(counties=['required']))
        make_error_event(applicant, dict(first_name=['required']))
        make_error_event(applicant, dict(last_name=['required']))
        self.assertTrue(
            made_a_meaningful_attempt_to_apply(applicant))

    def test_empty_forms_with_later_completed_county_form_returns_true(self):
        applicant = make_applicant()
        make_error_event(applicant, dict(counties=['required']))
        make_error_event(applicant, dict(first_name=['required']))
        make_county_form_completed_event(applicant)
        self.assertTrue(
            made_a_meaningful_attempt_to_apply(applicant))
