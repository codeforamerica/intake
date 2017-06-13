from unittest.mock import patch, Mock
from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from user_accounts.models import Organization
from intake import models, exceptions
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

    @patch('intake.services.pdf_service.fill_pdf_for_application')
    @patch('project.alerts.send_email_to_admins')
    def test_if_no_app_ids(self, admin_alert, fill_pdf):
        PDFService.fill_any_unfilled_pdfs_for_app_ids([])
        fill_pdf.assert_not_called()
        admin_alert.assert_not_called()

    @patch('intake.services.pdf_service.fill_pdf_for_application')
    @patch('project.alerts.send_email_to_admins')
    def test_if_all_apps_have_pdfs(self, admin_alert, fill_pdf):
        app_ids = []
        subs = []
        for i in range(3):
            sub = factories.FormSubmissionWithOrgsFactory(
                organizations=[Organization.objects.get(slug='sf_pubdef')])
            factories.FilledPDFFactory(submission=sub)
            subs.append(sub)
            app_ids.append(sub.applications.first().id)
        fill_pdf.assert_not_called()
        admin_alert.assert_not_called()

    @patch('intake.services.pdf_service.fill_pdf_for_application')
    @patch('project.alerts.send_email_to_admins')
    def test_if_some_apps_have_pdfs(self, admin_alert, fill_pdf):
        app_ids = []
        subs = []
        for i in range(3):
            sub = factories.FormSubmissionWithOrgsFactory(
                organizations=[Organization.objects.get(slug='sf_pubdef')])
            subs.append(sub)
            if i < 2:
                factories.FilledPDFFactory(submission=sub)
            app_ids.append(sub.applications.first().id)
        PDFService.fill_any_unfilled_pdfs_for_app_ids(app_ids)
        fill_pdf.assert_called_once_with(app_ids[2])
        printed_app = str(subs[2].applications.first())
        admin_alert.assert_called_once_with(
            subject='No FilledPDFs for Applications',
            message='1 apps did not have PDFs:\n{}'.format(printed_app))


class TestResetAppsForNewappsPdf(TestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.newapps_pdf = factories.NewAppsPDFFactory()

    def add_3_subs_to_newapps_pdf(self):
        subs = [
            factories.FormSubmissionWithOrgsFactory(
                organizations=[Organization.objects.get(slug='sf_pubdef')])
            for i in range(3)]
        apps = [sub.applications.first() for sub in subs]
        self.newapps_pdf.applications.add(*apps)
        return subs

    @patch('intake.services.pdf_service.fill_any_unfilled_pdfs_for_app_ids')
    @patch('intake.services.pdf_service.set_bytes_to_filled_pdfs')
    def test_that_existing_apps_are_reset(self, set_bytes, fill_pdfs):
        previous_apps = [
            sub.applications.first()
            for sub in self.add_3_subs_to_newapps_pdf()]
        new_sf_app = factories.FormSubmissionWithOrgsFactory(
                organizations=[Organization.objects.get(slug='sf_pubdef')]
        ).applications.first()
        PDFService.reset_apps_for_newapps_pdf(self.newapps_pdf, [new_sf_app])
        resulting_apps = list(self.newapps_pdf.applications.all())
        for app in previous_apps:
            self.assertNotIn(app, resulting_apps)
        self.assertIn(new_sf_app, resulting_apps)

    @patch('intake.services.pdf_service.fill_any_unfilled_pdfs_for_app_ids')
    @patch('intake.services.pdf_service.set_bytes_to_filled_pdfs')
    def test_if_no_apps(self, set_bytes, fill_pdfs):
        self.add_3_subs_to_newapps_pdf()
        PDFService.reset_apps_for_newapps_pdf(self.newapps_pdf, [])
        self.assertFalse(self.newapps_pdf.applications.all())
        self.assertEqual([], list(self.newapps_pdf.applications.all()))
        set_bytes.assert_called_once_with(self.newapps_pdf, [])
        fill_pdfs.assert_not_called()

    @patch('intake.services.pdf_service.fill_any_unfilled_pdfs_for_app_ids')
    @patch('intake.services.pdf_service.set_bytes_to_filled_pdfs')
    def test_if_existing_is_empty(self, set_bytes, fill_pdfs):
        PDFService.reset_apps_for_newapps_pdf(
            self.newapps_pdf, [])
        set_bytes.assert_called_once_with(self.newapps_pdf, [])
        fill_pdfs.assert_not_called()

    @patch('intake.services.pdf_service.fill_any_unfilled_pdfs_for_app_ids')
    @patch('intake.services.pdf_service.set_bytes_to_filled_pdfs')
    def test_if_one_app(self, set_bytes, fill_pdfs):
        self.add_3_subs_to_newapps_pdf()
        new_sf_sub = factories.FormSubmissionWithOrgsFactory(
                organizations=[Organization.objects.get(slug='sf_pubdef')])
        factories.FilledPDFFactory(submission=new_sf_sub)
        new_sf_app = new_sf_sub.applications.first()
        PDFService.reset_apps_for_newapps_pdf(self.newapps_pdf, [new_sf_app])
        self.assertEqual(
            [new_sf_app], list(self.newapps_pdf.applications.all()))
        fill_pdfs.assert_called_once_with([new_sf_app.id])
        self.assertEqual(set_bytes.call_count, 1)

    @patch('intake.services.pdf_service.fill_any_unfilled_pdfs_for_app_ids')
    @patch('intake.services.pdf_service.set_bytes_to_filled_pdfs')
    def test_if_multiple_apps(self, set_bytes, fill_pdfs):
        self.add_3_subs_to_newapps_pdf()
        new_sf_subs = [
            factories.FormSubmissionWithOrgsFactory(
                organizations=[Organization.objects.get(slug='sf_pubdef')])
            for i in range(3)]
        for sub in new_sf_subs:
            factories.FilledPDFFactory(submission=sub)
        new_sf_apps = [sub.applications.first() for sub in new_sf_subs]
        new_app_ids = [app.id for app in new_sf_apps]
        PDFService.reset_apps_for_newapps_pdf(self.newapps_pdf, new_sf_apps)
        self.assertEqual(
            set(new_sf_apps), set(self.newapps_pdf.applications.all()))
        fill_pdfs.assert_called_once_with(new_app_ids)
        self.assertEqual(set_bytes.call_count, 1)


class TestPrebuildNewappsPdfForSanFrancisco(TestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass()
        cls.sf = Organization.objects.get(slug='sf_pubdef')

    def test_if_sf_doesnt_exist(self):
        Organization.objects.filter(slug='sf_pubdef').delete()
        with self.assertRaises(ObjectDoesNotExist):
            PDFService.prebuild_newapps_pdf_for_san_francisco()

    @patch(
        'intake.services.applications_service.get_unread_applications_for_org')
    @patch('intake.services.pdf_service.reset_apps_for_newapps_pdf')
    def test_call_to_reset(self, reset_apps, get_unread_apps):
        get_unread_apps.return_value = []
        PDFService.prebuild_newapps_pdf_for_san_francisco()
        self.assertEqual(reset_apps.call_count, 1)

    @patch(
        'intake.services.applications_service.get_unread_applications_for_org')
    @patch('intake.services.pdf_service.reset_apps_for_newapps_pdf')
    def test_creates_newapps_pdf_if_it_doesnt_exist(
            self, reset_apps, get_unread_apps):
        newapps_count = models.NewAppsPDF.objects.count()
        self.assertEqual(0, newapps_count)
        PDFService.prebuild_newapps_pdf_for_san_francisco()
        self.assertEqual(reset_apps.call_count, 1)
        newapps_count = models.NewAppsPDF.objects.count()
        self.assertEqual(1, newapps_count)


class TestFillPdfForApplication(TestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        sub = factories.FormSubmissionWithOrgsFactory(
            organizations=[Organization.objects.get(slug='sf_pubdef')])
        cls.app = sub.applications.first()

    def test_if_app_not_found(self):
        with self.assertRaises(ObjectDoesNotExist):
            PDFService.fill_pdf_for_application(98761)

    def test_with_no_fillable_pdf(self):
        with self.assertRaises(exceptions.MissingFillablePDFError):
            PDFService.fill_pdf_for_application(self.app.id)

    def test_if_fillable_pdf_is_empty(self):
        fillable = factories.FillablePDFFactory()
        fillable.pdf = None
        fillable.save()
        with self.assertRaises(exceptions.MissingFillablePDFError):
            PDFService.fill_pdf_for_application(self.app.id)

    @patch('intake.models.FillablePDF.fill')
    @patch('intake.models.FilledPDF.create_with_pdf_bytes')
    def test_if_app_and_fillable_are_okay(self, create_w_bytes, mock_fill):
        fillable = factories.FillablePDFFactory()
        mock_fill.return_value = b'yay bytez'
        PDFService.fill_pdf_for_application(self.app.id)
        create_w_bytes.assert_called_once_with(
            pdf_bytes=b'yay bytez',
            original_pdf=fillable,
            submission=self.app.form_submission)


class TestRebuildNewappsPdfForNewApplication(TestCase):

    @patch(
        'intake.services.pdf_service.prebuild_newapps_pdf_for_san_francisco')
    def test_when_newapps_pdf_does_not_exist(self, prebuild):
        sub = factories.FormSubmissionWithOrgsFactory(
            organizations=[Organization.objects.get(slug='sf_pubdef')])
        app = sub.applications.first()
        PDFService.rebuild_newapps_pdf_for_new_application(app.id)
        prebuild.assert_called_once_with()

    @patch(
        'intake.services.pdf_service.prebuild_newapps_pdf_for_san_francisco')
    def test_when_new_app_not_in_prebuilt(self, prebuild):
        sub = factories.FormSubmissionWithOrgsFactory(
            organizations=[Organization.objects.get(slug='sf_pubdef')])
        app = sub.applications.first()
        factories.NewAppsPDFFactory()
        PDFService.rebuild_newapps_pdf_for_new_application(app.id)
        prebuild.assert_called_once_with()

    @patch(
        'intake.services.pdf_service.prebuild_newapps_pdf_for_san_francisco')
    def test_when_new_app_in_prebuilt(self, prebuild):
        sub = factories.FormSubmissionWithOrgsFactory(
            organizations=[Organization.objects.get(slug='sf_pubdef')])
        app = sub.applications.first()
        newapps_pdf = factories.NewAppsPDFFactory()
        newapps_pdf.applications.add(app)
        PDFService.rebuild_newapps_pdf_for_new_application(app.id)
        prebuild.assert_not_called()


class TestRebuildNewappsPdfForRemovedApplication(TestCase):

    @patch(
        'intake.services.pdf_service.prebuild_newapps_pdf_for_san_francisco')
    def test_when_newapps_pdf_does_not_exist(self, prebuild):
        sub = factories.FormSubmissionWithOrgsFactory(
            organizations=[Organization.objects.get(slug='sf_pubdef')])
        app = sub.applications.first()
        PDFService.rebuild_newapps_pdf_for_removed_application(app.id)
        prebuild.assert_not_called()

    @patch(
        'intake.services.pdf_service.prebuild_newapps_pdf_for_san_francisco')
    def test_when_new_app_not_in_prebuilt(self, prebuild):
        sub = factories.FormSubmissionWithOrgsFactory(
            organizations=[Organization.objects.get(slug='sf_pubdef')])
        app = sub.applications.first()
        factories.NewAppsPDFFactory()
        PDFService.rebuild_newapps_pdf_for_removed_application(app.id)
        prebuild.assert_not_called()

    @patch(
        'intake.services.pdf_service.prebuild_newapps_pdf_for_san_francisco')
    def test_when_new_app_in_prebuilt(self, prebuild):
        sub = factories.FormSubmissionWithOrgsFactory(
            organizations=[Organization.objects.get(slug='sf_pubdef')])
        app = sub.applications.first()
        newapps_pdf = factories.NewAppsPDFFactory()
        newapps_pdf.applications.add(app)
        PDFService.rebuild_newapps_pdf_for_removed_application(app.id)
        prebuild.assert_called_once_with()
