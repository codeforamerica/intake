from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock

from intake.tests import mock
# from intake.translators import fields

class TestTranslators(TestCase):

    def test_clean_slate(self):
        old, new = mock.pdf_fillable_models()
        expected = mock.PDF_FILLABLE_DATA
        from intake.translators import clean_slate
        old_results = clean_slate.translator(old)
        new_results = clean_slate.translator(new)
        try:
            self.assertDictEqual(old_results, expected)
            self.assertDictEqual(new_results, expected)
        except AssertionError as error:
            import ipdb; ipdb.set_trace()
            raise error


    # def test_yes_no_radio_field(self):
    #     yes_inputs = [
    #         'yes', 'Yes', 'YES',
    #         True, 1 ]
    #     no_inputs = [
    #         'no', 'No', 'NO',
    #         False, 0 ]
    #     off_inputs = [
    #         'off', 'Off', 'OFF', 'oFf',
    #         '', ' ', '\n', 'ndadsliajfnieuniub',
    #         -1, 543
    #     ]

    #     field = fields.YesNoRadioField()
    #     for val in yes_inputs:
    #         self.assertEqual(field(val), 'Yes')
    #     for val in no_inputs:
    #         self.assertEqual(field(val), 'No')
    #     for val in off_inputs:
    #         self.assertEqual(field(val), 'Off')

