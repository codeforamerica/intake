import os
import sys
from subprocess import Popen, PIPE, STDOUT
from django.conf import settings
from django.db import connections


def aws_open(command):
    env = os.environ.copy()
    env.update({
        "AWS_ACCESS_KEY_ID": settings.SYNC_AWS_ID,
        "AWS_SECRET_ACCESS_KEY": settings.SYNC_AWS_KEY,
    })
    task = Popen(command, env=env)
    return task.wait()


def pg_dump(file_location):
    env = os.environ.copy()
    env.update({  # requires having password set to test
        "PGPASSWORD": settings.DATABASES['default']['PASSWORD']
    })
    pg_dump = [
        'pg_dump',
        '-h%s' % 'localhost',
        '-U%s' % settings.DATABASES['default']['USER'],
        settings.DATABASES['default']['NAME']
    ]
    with Popen(pg_dump, env=env, stdout=PIPE, stderr=STDOUT, bufsize=1
               ) as task, open(file_location, 'ab') as f:
        for line in task.stdout:
            f.write(line)
        return task.wait()


def pg_load(file_location):
    env = os.environ.copy()
    env.update({  # requires having password set to test
        "PGPASSWORD": settings.DATABASES['default']['PASSWORD']
    })
    load = [
        'psql',
        '-h%s' % 'localhost',
        '-U%s' % settings.DATABASES['default']['USER'],
        '-d%s' % settings.DATABASES['default']['NAME'],
        '-f%s' % file_location,
    ]
    task = Popen(load, env=env)
    return task.wait()


def run_sql(query):
    with connections['default'].cursor() as cursor:
        cursor.execute(query)
