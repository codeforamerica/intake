import os
from subprocess import Popen
from django.conf import settings


def aws_open(command):
    env = os.environ.copy()
    env.update({
        "AWS_ACCESS_KEY_ID": settings.SYNC_AWS_ID,
        "AWS_SECRET_ACCESS_KEY": settings.SYNC_AWS_KEY,
    })
    Popen(command, env=env)
