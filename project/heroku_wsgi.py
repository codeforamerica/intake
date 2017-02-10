import os
from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings.prod")
application = DjangoWhiteNoise(get_wsgi_application())
