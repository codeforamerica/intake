import dj_database_url
import psycopg2
from intake import models
from django.contrib.auth.models import User


USERS_SQL = '''
select * from auth_user;
'''

SUBMISSIONS_SQL = '''
select * from form_filler_submission;
'''

LOGS_SQL = '''
select * from form_filler_logentry where event_type != 'received';
'''

user_map = {
    'bgolder': 'bgolder@codeforamerica.org',
    'jazmyn': 'jazmyn@codeforamerica.org'
}

event_type_map = {
    'added': models.ApplicationLogEntry.PROCESSED,
    'opened': models.ApplicationLogEntry.OPENED,
    'referred': models.ApplicationLogEntry.REFERRED
}

class DataImporter:

    def __init__(self, import_from='', ssl=False):
        config = dj_database_url.parse(import_from)
        self.config = dict(
            database=config.get('NAME', 'typeseam'),
            user=config.get('USER', 'postgres'),
            password=config.get('PASSWORD', ''),
            host=config.get('HOST', 'localhost'),
            port=config.get('PORT', 5432)
            )
        if ssl:
            self.config['sslmode'] = 'require'
        self._connection = psycopg2.connect(**self.config)
        self._cursor = self._connection.cursor(
            cursor_factory=psycopg2.extras.DictCursor)
        self._uuid_pk_map = {}
        self._email_pk_map = {}
        self.messages = []

    def report(self):
        return '\n--------\n'.join(self.messages)

    def from_string(self):
        return ' from `{}` on `{}`'.format(self.config['database'], self.config['host'])

    def import_records(self, delete_existing=False):
        self.messages.append("Beginning data import {}".format(self.from_string()))
        self.import_users()
        self.import_submissions(delete_existing)
        self.import_logs(delete_existing)

    def delete_existing(self, model, flag):
        if flag:
            count = model.objects.count()
            if not count:
                delete_message = "No {} instances exist. Not deleting anything.".format(model.__name__)
            else:
                model.objects.all().delete()
                delete_message = "Deleted {} existing {} instances".format(count, model.__name__)
            self.messages.append(delete_message)

    def parse_user(self, record):
        email = record['email']
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            return 'found', existing_user
        else:
            return 'created', User.objects.create_user(
                username=email.split('@')[0],
                email=email)

    def import_users(self):
        self._cursor.execute(USERS_SQL)
        user_imports = [self.parse_user(record) for record in self._cursor]
        success_message = 'Successfully imported {} users:'.format(len(user_imports))
        for created, user in user_imports:
            self._email_pk_map[user.email] = user.id
            success_message += '\n\t{} {}'.format(created, user.email)
        self.messages.append(success_message)

    def import_submissions(self, delete_existing=False):
        self.delete_existing(models.FormSubmission, delete_existing)
        self._cursor.execute(SUBMISSIONS_SQL)
        result = models.FormSubmission.objects.bulk_create(
            self.parse_submission(r) for r in self._cursor
        )
        success_message = "Successfully imported {} form submissions{}".format(
                len(result), self.from_string())
        saved_submissions = models.FormSubmission.objects.all()
        for sub in saved_submissions:
            self._uuid_pk_map[sub.old_uuid] = sub.id
        self.messages.append(success_message)

    def parse_submission(self, record):
        return models.FormSubmission(
            old_uuid=record['uuid'],
            date_received=record['date_received'],
            answers=record['answers']
            )

    def import_logs(self, delete_existing=False):
        self.delete_existing(models.ApplicationLogEntry, delete_existing)
        self._cursor.execute(LOGS_SQL)
        result = models.ApplicationLogEntry.objects.bulk_create(
            self.parse_log(r) for r in self._cursor
            )
        success_message = "Successfully imported {} event logs{}".format(
                len(result), self.from_string())
        self.messages.append(success_message)

    def parse_log(self, record):
        if record['user'] in user_map:
            email = user_map[record['user']]
        else:
            email = record['user']
        return models.ApplicationLogEntry(
            time=record['datetime'],
            user_id=self._email_pk_map.get(email, None),
            submission_id=self._uuid_pk_map.get(record['submission_key'], None),
            event_type=event_type_map[record['event_type']]
            )

        

