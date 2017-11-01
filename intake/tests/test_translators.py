from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock

from intake.tests import mock
from intake.translators import fields


class TestTranslators(TestCase):

    def test_clean_slate(self):
        old, new = pdf_fillable_models()
        expected = PDF_FILLABLE_DATA
        from intake.translators import clean_slate
        old_results = clean_slate.translator(old)
        new_results = clean_slate.translator(new)
        self.assertDictEqual(old_results, expected)
        self.assertDictEqual(new_results, expected)

    def test_yes_no_radio_field(self):
        yes_inputs = [
            'yes', 'Yes', 'YES',
            True, 1]
        no_inputs = [
            'no', 'No', 'NO',
            False, 0]
        off_inputs = [
            'off', 'Off', 'OFF', 'oFf',
            '', ' ', '\n', 'ndadsliajfnieuniub',
            -1, 543
        ]

        field = fields.YesNoRadioField()
        for val in yes_inputs:
            self.assertEqual(field(val), 'Yes')
        for val in no_inputs:
            self.assertEqual(field(val), 'No')
        for val in off_inputs:
            self.assertEqual(field(val), 'Off')


def pdf_fillable_models():
    """Creates mock objects that are fed to the form to pdf translator
    """
    new_model_for_pdf = Mock(
        answers=dict(
            contact_preferences=[
                'prefers_email',
                'prefers_sms',
                'prefers_snailmail'],
            address=dict(
                street='111 Main St.',
                city='Oakland',
                state='CA',
                zip='94609'),
            rap_outside_sf='yes',
            phone_number='510-415-0000',
            being_charged='no',
            dob=dict(month='2', day='1', year='82'),
            when_where_outside_sf='2004',
            email='someone@gmail.com',
            currently_employed='yes',
            first_name='Foo',
            middle_name='Gaz',
            last_name='Bar',
            how_did_you_hear='A friend',
            on_probation_parole='yes',
            where_probation_or_parole='contra costa',
            when_probation_or_parole='2017',
            monthly_income='1800',
            monthly_expenses='1800',
            ssn='999999999',
            us_citizen='yes',
            serving_sentence='no',
        ))

    old_model_for_pdf = Mock(
        answers=dict(
            contact_preferences=[
                'prefers_email', 'prefers_sms', 'prefers_snailmail'],
            address_street='111 Main St.',
            address_city='Oakland',
            address_state='CA',
            address_zip='94609',
            rap_outside_sf='yes',
            phone_number='510-415-0000',
            being_charged='no',
            dob_month='2',
            dob_day='1',
            dob_year='82',
            when_where_outside_sf='2004',
            email='someone@gmail.com',
            currently_employed='yes',
            first_name='Foo',
            middle_name='Gaz',
            last_name='Bar',
            how_did_you_hear='A friend',
            on_probation_parole='yes',
            where_probation_or_parole='contra costa',
            when_probation_or_parole='2017',
            monthly_income='1800',
            monthly_expenses='1800',
            ssn='999999999',
            us_citizen='yes',
            serving_sentence='no',
        ))
    for model in [old_model_for_pdf, new_model_for_pdf]:
        model.get_local_date_received.return_value = '6/11/2016'

    return old_model_for_pdf, new_model_for_pdf


# the data that should be output by the form to pdf translator
PDF_FILLABLE_DATA = {
    'Address City': 'Oakland',
    'Address State': 'CA',
    'Address Street': '111 Main St.',
    'Address Zip': '94609',
    'Arrested outside SF': 'Yes',
    'Cell phone number': '510-415-0000',
    'Charged with a crime': 'No',
    'DOB': '2/1/82',
    'Date': '6/11/2016',
    'Date of Birth': '2/1/82',
    'Dates arrested outside SF': '2004',
    'Email Address': 'someone@gmail.com',
    'Employed': 'Yes',
    'First Name': 'Foo',
    'FirstName': 'Foo',
    'Home phone number': '',
    'How did you hear about the Clear My Record Program': 'A friend',
    'If probation where and when?': 'contra costa 2017',
    'Last Name': 'Bar',
    'LastName': 'Bar',
    'MI': 'G',
    'May we leave voicemail': 'Off',
    'May we send mail here': 'Off',
    'Monthly expenses': '1800',
    'On probation or parole': 'Yes',
    'Other phone number': '',
    'SSN': 'SS# 999-99-9999',
    'Serving a sentence': 'No',
    'Social Security Number': '999-99-9999',
    'US Citizen': 'Yes',
    'What is your monthly income': '1800',
    'Work phone number': ''}
