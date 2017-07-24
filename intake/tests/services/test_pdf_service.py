from unittest.mock import patch, Mock
from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from user_accounts.models import Organization
from intake import models, exceptions
from intake.services import pdf_service as PDFService
from intake.tests import factories


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


class TestSetBytesToFilledPdfs(TestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.instance = factories.PrebuiltPDFBundleFactory()

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


class TestGetPrebuiltPdfBundleForAppIdSet(TestCase):

    def test_if_no_pdf_bundles_exist(self):
        apps = factories.make_app_ids_for_sf()
        result = PDFService.get_prebuilt_pdf_bundle_for_app_id_set(apps)
        self.assertEqual(None, result)

    def test_if_pdf_bundle_exists_for_some_apps(self):
        prebuilt = factories.PrebuiltPDFBundleFactory()
        matching_apps = factories.make_app_ids_for_sf()
        prebuilt.applications.add(*matching_apps)
        not_matching_apps = factories.make_app_ids_for_sf()
        apps = matching_apps + not_matching_apps
        result = PDFService.get_prebuilt_pdf_bundle_for_app_id_set(apps)
        self.assertEqual(None, result)

    def test_if_pdf_bundle_exists_for_all_apps(self):
        prebuilt = factories.PrebuiltPDFBundleFactory()
        matching_apps = factories.make_app_ids_for_sf()
        prebuilt.applications.add(*matching_apps)
        result = PDFService.get_prebuilt_pdf_bundle_for_app_id_set(
            matching_apps)
        self.assertEqual(prebuilt, result)

    def test_if_no_apps(self):
        prebuilt = factories.PrebuiltPDFBundleFactory()
        matching_apps = factories.make_app_ids_for_sf()
        prebuilt.applications.add(*matching_apps)
        result = PDFService.get_prebuilt_pdf_bundle_for_app_id_set([])
        self.assertEqual(None, result)

    def test_bundles_with_same_count_but_different_apps_are_excluded(self):
        other_prebuilt = factories.PrebuiltPDFBundleFactory()
        not_matching_apps = factories.make_app_ids_for_sf(count=2)
        other_prebuilt.applications.add(*not_matching_apps)

        expected_prebuilt = factories.PrebuiltPDFBundleFactory()
        matching_apps = factories.make_app_ids_for_sf(count=2)
        expected_prebuilt.applications.add(*matching_apps)

        result = PDFService.get_prebuilt_pdf_bundle_for_app_id_set(
            matching_apps)
        self.assertNotEqual(other_prebuilt, result)
        self.assertEqual(expected_prebuilt, result)


class TestGetOrCreatePrebuiltPdfForAppIds(TestCase):

    @patch(
        'intake.services.pdf_service.get_prebuilt_pdf_bundle_for_app_id_set')
    @patch('intake.services.pdf_service.update_pdf_bundle_for_san_francisco')
    @patch('project.alerts.send_email_to_admins')
    def test_if_prebuilt_does_not_exist(
            self, admin_alert, update_pdf, get_prebuilt):
        get_prebuilt.return_value = None
        fake_app_ids = [32, 52, 12]
        result = PDFService.get_or_create_prebuilt_pdf_for_app_ids(
            fake_app_ids)
        update_pdf.assert_called_once_with()
        self.assertEqual(update_pdf.return_value, result)
        self.assertEqual(1, admin_alert.call_count)
        get_prebuilt.assert_called_once_with(fake_app_ids)

    @patch(
        'intake.services.pdf_service.get_prebuilt_pdf_bundle_for_app_id_set')
    @patch('intake.services.pdf_service.update_pdf_bundle_for_san_francisco')
    @patch('project.alerts.send_email_to_admins')
    def test_if_prebuilt_exists(
            self, admin_alert, update_pdf, get_prebuilt):
        mock_prebuilt = Mock()
        get_prebuilt.return_value = mock_prebuilt
        fake_app_ids = [32, 52, 12]
        result = PDFService.get_or_create_prebuilt_pdf_for_app_ids(
            fake_app_ids)
        self.assertEqual(mock_prebuilt, result)
        update_pdf.assert_not_called()
        admin_alert.assert_not_called()
        get_prebuilt.assert_called_once_with(fake_app_ids)


class TestCreateNewPdfBundleForApps(TestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass()
        cls.sf = Organization.objects.get(slug='sf_pubdef')

    @patch('intake.services.pdf_service.fill_any_unfilled_pdfs_for_app_ids')
    @patch('intake.services.pdf_service.set_bytes_to_filled_pdfs')
    def test_if_no_apps(self, set_bytes, fill_pdfs):
        result = PDFService.create_new_pdf_bundle_for_apps(self.sf, [])
        self.assertFalse(result.applications.all())
        self.assertEqual([], list(result.applications.all()))
        self.assertEqual(1, set_bytes.call_count)
        fill_pdfs.assert_called_once_with([])

    @patch('intake.services.pdf_service.fill_any_unfilled_pdfs_for_app_ids')
    @patch('intake.services.pdf_service.set_bytes_to_filled_pdfs')
    def test_if_one_app(self, set_bytes, fill_pdfs):
        new_sf_sub = factories.FormSubmissionWithOrgsFactory(
                organizations=[Organization.objects.get(slug='sf_pubdef')])
        factories.FilledPDFFactory(submission=new_sf_sub)
        new_sf_app = new_sf_sub.applications.first()
        result = PDFService.create_new_pdf_bundle_for_apps(
            self.sf, [new_sf_app])
        self.assertEqual(
            [new_sf_app], list(result.applications.all()))
        fill_pdfs.assert_called_once_with([new_sf_app.id])
        self.assertEqual(set_bytes.call_count, 1)

    @patch('intake.services.pdf_service.fill_any_unfilled_pdfs_for_app_ids')
    @patch('intake.services.pdf_service.set_bytes_to_filled_pdfs')
    def test_if_multiple_apps(self, set_bytes, fill_pdfs):
        new_sf_subs = [
            factories.FormSubmissionWithOrgsFactory(
                organizations=[Organization.objects.get(slug='sf_pubdef')])
            for i in range(3)]
        for sub in new_sf_subs:
            factories.FilledPDFFactory(submission=sub)
        new_sf_apps = [sub.applications.first() for sub in new_sf_subs]
        new_app_ids = [app.id for app in new_sf_apps]
        result = PDFService.create_new_pdf_bundle_for_apps(
            self.sf, new_sf_apps)
        self.assertEqual(
            set(new_sf_apps), set(result.applications.all()))
        fill_pdfs.assert_called_once_with(new_app_ids)
        self.assertEqual(set_bytes.call_count, 1)


class TestUpdatePdfBundleForSanFrancisco(TestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass()
        cls.sf = Organization.objects.get(slug='sf_pubdef')

    def setUp(self):
        super().setUp()
        self.set_bytes_patcher = patch(
            'intake.services.pdf_service.set_bytes_to_filled_pdfs')
        self.set_bytes_patcher.start()
        self.fill_pdfs_patcher = patch(
            'intake.services.pdf_service.fill_any_unfilled_pdfs_for_app_ids')
        self.fill_pdfs_patcher.start()

    def tearDown(self):
        self.fill_pdfs_patcher.stop()
        self.set_bytes_patcher.stop()
        super().tearDown()

    def test_if_sf_doesnt_exist(self):
        Organization.objects.filter(slug='sf_pubdef').delete()
        with self.assertRaises(ObjectDoesNotExist):
            PDFService.update_pdf_bundle_for_san_francisco()

    @patch(
        'intake.services.applications_service.get_unread_applications_for_org')
    def test_if_no_unread(self, get_unread_apps):
        get_unread_apps.return_value = factories.apps_queryset([])
        PDFService.update_pdf_bundle_for_san_francisco()

    @patch(
        'intake.services.applications_service.get_unread_applications_for_org')
    @patch('intake.services.pdf_service.create_new_pdf_bundle_for_apps')
    def test_if_unread_set_has_a_match(self, create_bundle, get_unread_apps):
        apps = factories.make_apps_for_sf()
        prebuilt = factories.PrebuiltPDFBundleFactory()
        prebuilt.applications.add(*apps)
        get_unread_apps.return_value = factories.apps_queryset(apps)
        result = PDFService.update_pdf_bundle_for_san_francisco()
        self.assertEqual(result, prebuilt)
        create_bundle.assert_not_called()

    @patch(
        'intake.services.applications_service.get_unread_applications_for_org')
    def test_creates_pdf_bundle_if_no_match(self, get_unread_apps):
        matching_apps = factories.make_apps_for_sf()
        not_matching_apps = factories.make_apps_for_sf()
        prebuilt = factories.PrebuiltPDFBundleFactory()
        prebuilt.applications.add(*matching_apps)
        all_apps = matching_apps + not_matching_apps
        get_unread_apps.return_value = factories.apps_queryset(all_apps)
        result = PDFService.update_pdf_bundle_for_san_francisco()
        self.assertNotEqual(result, prebuilt)
        self.assertEqual(set(all_apps), set(result.applications.all()))

    @patch(
        'intake.services.applications_service.get_unread_applications_for_org')
    def test_creates_pdf_bundle_if_no_prebuilts(self, get_unread_apps):
        apps = factories.make_apps_for_sf()
        get_unread_apps.return_value = factories.apps_queryset(apps)
        prebuilt_count = models.PrebuiltPDFBundle.objects.count()
        self.assertEqual(0, prebuilt_count)
        PDFService.update_pdf_bundle_for_san_francisco()
        prebuilt_count = models.PrebuiltPDFBundle.objects.count()
        self.assertEqual(1, prebuilt_count)


class TestRebuildNewappsPdfForRemovedApplication(TestCase):

    @patch(
        'intake.services.pdf_service.update_pdf_bundle_for_san_francisco')
    def test_when_opened_app_is_for_sf(self, update_pdf):
        sub = factories.FormSubmissionWithOrgsFactory(
            organizations=[Organization.objects.get(slug='sf_pubdef')])
        app = sub.applications.first()
        factories.FillablePDFFactory()
        PDFService.rebuild_pdf_bundle_for_removed_application(app.id)
        update_pdf.assert_called_once_with()

    @patch(
        'intake.services.pdf_service.update_pdf_bundle_for_san_francisco')
    def test_when_opened_app_is_for_not_sf(self, update_pdf):
        sub = factories.FormSubmissionWithOrgsFactory(
            organizations=[Organization.objects.get(slug='a_pubdef')])
        app = sub.applications.first()
        factories.FillablePDFFactory()
        PDFService.rebuild_pdf_bundle_for_removed_application(app.id)
        update_pdf.assert_not_called()
