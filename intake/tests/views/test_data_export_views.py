import csv
import io
from datetime import datetime
from django.urls import reverse
from django.conf import settings
from django.test import TestCase

from intake.constants import PACIFIC_TIME
from intake.models import StatusType
from intake.tests import factories as intake_factories
from intake.tests.fake_answers_dictionary import ebclc_answers
from user_accounts.tests import factories as accounts_factories
from user_accounts.models import Organization


class TestCSVDownloadView(TestCase):
    view_name = 'intake-csv_download'
    fixtures = ['template_options', 'groups', 'counties', 'organizations']

    def test_anon_is_redirected_to_login(self):
        response = self.client.get(reverse(self.view_name))
        self.assertIn(reverse('user_accounts-login'), response.url)
        self.assertEqual(response.status_code, 302)

    def test_user_sees_correct_columns_and_data_in_csv(self):
        user = accounts_factories.app_reviewer('ebclc').user
        ebclc = Organization.objects.get(slug='ebclc')
        sub = intake_factories.FormSubmissionWithOrgsFactory(
            organizations=[ebclc], answers=ebclc_answers)
        app = sub.applications.first()
        update_1 = intake_factories.StatusUpdateFactory(
            application=app,
            status_type=StatusType.objects.get(slug='eligible'),
            author=user
        )
        update_1.created = PACIFIC_TIME.localize(datetime(2017, 1, 1))
        update_1.save()
        update_2 = intake_factories.StatusUpdateFactory(
            application=app,
            status_type=StatusType.objects.get(slug='granted'),
            author=user
        )
        update_2.created = PACIFIC_TIME.localize(datetime(2017, 1, 2))
        update_2.save()
        self.client.login(
            username=user.username, password=settings.TEST_USER_PASSWORD)
        response = self.client.get(reverse(self.view_name))
        self.assertEqual(200, response.status_code)
        result = response.content.decode('utf-8')
        expected_result_line_1 = str(
            'id,Link,Application Date,Applied on,Wants help with record in,'
            'Preferred contact methods,First name,Middle name,'
            'Last name,Preferred pronouns,Phone number,Alternate phone number,'
            'Email,Address,Date of birth,Citizenship status,'
            'Is currently being charged,Is serving a sentence,'
            'Is on probation or parole,Finished half probation,'
            'Reduced probation,RAP in other counties,Where/when,'
            'Has suspended license,Owes court fines/fees,'
            'Has been denied housing or employment,'
            'Denied housing/employment by,Seeking job that requires LiveScan,'
            'Registered under PC 290,'
            'Monthly income,On public benefits,Owns home,Household size,'
            'Reasons for applying,How they found out about this,'
            'Additional information,'
            'Understands might not qualify and could take a few months,'
            '"Consents to record access, filing, and court representation",'
            'Was transferred out,Has been opened,Latest status,'
            'Latest status date,Latest status author,Status history link')
        expected_result_line_2 = str(
            'Alameda,Text Message,Gabriel,Tiffany,Jenkins,She/Her/Hers,'
            '(415) 212-4848,(415) 212-4848,cmrtestuser@gmail.com,'
            '"6230 Shawn View\nNorth John, VA\n80973",4/19/1983,'
            'Other/I don\'t know,No,No,Yes,Not on probation,Not on probation,'
            'No,,No,No,,,,,"$3,001.00",No,Yes,3,,from work,I want help,'
            '"Yes, I understand","Yes, I give them permission to do that",'
            'False,False,Granted,01/02/2017,cmrtestuser+ebclc@gmail.com,')
        self.assertIn(expected_result_line_1, result)
        self.assertTrue(result.startswith(expected_result_line_1))
        self.assertIn(expected_result_line_2, result)

    def test_followup_staff_gets_not_listed_apps(self):
        user = accounts_factories.followup_user().user
        cfa_apps = intake_factories.make_apps_for('cfa', count=1)
        ebclc_apps = intake_factories.make_apps_for('ebclc', count=1)
        self.client.login(
            username=user.username, password=settings.TEST_USER_PASSWORD)
        response = self.client.get(reverse(self.view_name))
        self.assertEqual(200, response.status_code)
        reader = csv.DictReader(io.StringIO(response.content.decode('utf-8')))
        ids = []
        for row in reader:
            ids.append(int(row['id']))
        for app in cfa_apps:
            with self.subTest(app=app):
                self.assertIn(app.form_submission_id, ids)
        for app in ebclc_apps:
            with self.subTest(app=app):
                self.assertNotIn(app.form_submission_id, ids)

    def test_org_user_gets_apps_from_own_org_only(self):
        user = accounts_factories.app_reviewer('ebclc').user
        cc_apps = intake_factories.make_apps_for('cc_pubdef', count=1)
        ebclc_apps = intake_factories.make_apps_for('ebclc', count=1)
        self.client.login(
            username=user.username, password=settings.TEST_USER_PASSWORD)
        response = self.client.get(reverse(self.view_name))
        self.assertEqual(200, response.status_code)
        reader = csv.DictReader(io.StringIO(response.content.decode('utf-8')))
        ids = []
        for row in reader:
            ids.append(int(row['id']))
        for app in cc_apps:
            with self.subTest(app=app):
                self.assertNotIn(app.form_submission_id, ids)
        for app in ebclc_apps:
            with self.subTest(app=app):
                self.assertIn(app.form_submission_id, ids)

    def test_org_user_w_no_apps_gets_empty_csv(self):
        user = accounts_factories.app_reviewer('ebclc').user
        cfa_apps = intake_factories.make_apps_for('cc_pubdef', count=1)
        self.client.login(
            username=user.username, password=settings.TEST_USER_PASSWORD)
        response = self.client.get(reverse(self.view_name))
        self.assertEqual(200, response.status_code)
        reader = csv.DictReader(io.StringIO(response.content.decode('utf-8')))
        rows = []
        for row in reader:
            rows.append(row)
        self.assertEqual(len(rows), 0)
