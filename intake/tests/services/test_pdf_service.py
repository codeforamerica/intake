from unittest.mock import patch
from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from django.core import mail
from user_accounts.models import Organization
from intake.services import pdf_service as PDFService
from intake.tests import factories


class TestSetBytesToFilledPdfs(TestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.instance = factories.NewAppsPDFFactory()

    @patch('intake.models.get_parser')
    def test_with_no_filled_pdfs(self, get_parser):
        PDFService.set_bytes_to_filled_pdfs(self.instance, [])
        self.assertFalse(self.instance.pdf)
        self.assertEqual(self.instance.pdf, None)
        get_parser.assert_not_called()

    @patch('intake.models.get_parser')
    def test_with_one_filled_pdf(self, get_parser):
        filled_pdf = factories.FilledPDFFactory()
        PDFService.set_bytes_to_filled_pdfs(self.instance, [filled_pdf])
        get_parser.assert_not_called()
        self.assertTrue(self.instance.pdf)
        filled_pdf.pdf.seek(0)
        self.assertEqual(self.instance.pdf.read(), filled_pdf.pdf.read())

    @patch('intake.models.get_parser')
    def test_with_multiple_filled_pdfs(self, get_parser):
        get_parser.return_value.join_pdfs.return_value = b'joined pdf'
        filled_pdfs = factories.FilledPDFFactory.create_batch(2)
        PDFService.set_bytes_to_filled_pdfs(self.instance, filled_pdfs)
        self.assertEqual(self.instance.pdf.read(), b'joined pdf')


class TestFillAnyUnfilledPdfsForAppIds(TestCase):

    def test_if_no_app_ids(self):
        raise NotImplementedError

    def test_if_some_apps_have_pdfs(self):
        raise NotImplementedError

    def test_if_all_apps_have_pdfs(self):
        raise NotImplementedError


class TestResetAppsForNewappsPdf(TestCase):

    def test_if_no_apps(self):
        raise NotImplementedError

    def test_if_one_app(self):
        raise NotImplementedError

    def test_if_multiple_apps(self):
        raise NotImplementedError


class TestPrebuildNewappsPdfForSanFrancisco(TestCase):

    def setUp(self):
        super().setUp()
        self.sf = Organization.objects.get(slug='sf_pubdef')

    def test_if_sf_doesnt_exist(self):
        Organization.objects.filter(slug='sf_pubdef').delete()
        with self.assertRaises(ObjectDoesNotExist):
            PDFService.prebuild_newapps_pdf_for_san_francisco()

    def test_if_no_unread_apps(self):
        factories.NewAppsPDFFactory()
        PDFService.prebuild_newapps_pdf_for_san_francisco()

    def test_if_some_unread_have_filled_pdfs(self):
        pass

    def test_if_no_unread_have_filled_pdfs(self):
        pass

    def test_if_all_unread_have_filled_pdfs(self):
        pass

    def test_app_ids_are_properly_linked(self):
        pass

    def test_that_pdf_is_properly_set(self):
        pass

    def test_if_newapps_pdf_doesnt_exist(self):
        pass


class TestFillPdfForApplication(TestCase):

    def test_if_app_not_found(self):
        pass

    def test_with_no_fillable_pdf(self):
        pass

    def test_if_fillable_pdf_is_empty(self):
        pass

    def test_if_app_and_fillable_are_okay(self):
        pass


class TestRebuildNewappsPdfForNewApplication(TestCase):
    def test_when_new_app_not_in_prebuilt(self):
        pass

    def test_when_new_app_in_prebuilt(self):
        pass


class TestRebuildNewappsPdfForRemovedApplication(TestCase):
    def test_when_new_app_not_in_prebuilt(self):
        pass

    def test_when_new_app_in_prebuilt(self):
        pass
