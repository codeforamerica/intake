from django.test import TestCase
from user_accounts.models import Organization
from intake.services import pdf_service as PDFService
from intake.tests import factories


class TestSetSinglePrebuiltPdfToBytes(TestCase):

    def test_if_multiple_prebuilts(self):
        pass

    def test_filename_is_correct(self):
        pass

    def test_pdf_saved_properly(self):
        pass


class TestPrebuildNewappsPdfForSanFrancisco(TestCase):

    def setUp(self):
        super().setUp()
        self.sf = Organization.objects.get(slug='sf_pubdef')

    def test_if_sf_doesnt_exist(self):
        Organization.objects.filter(slug='sf_pubdef').delete()
        PDFService.prebuild_newapps_pdf_for_san_francisco()

    def test_if_no_unread_apps(self):
        factories.FormSubmissionWithOrgsFactory(
            organizations=[self.sf])
        PDFService.prebuild_newapps_pdf_for_san_francisco()

    def test_if_some_unread_have_filled_pdfs(self):
        pass

    def test_if_no_unread_have_filled_pdfs(self):
        pass

    def test_if_all_unread_have_filled_pdfs(self):
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
