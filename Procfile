release: python manage.py migrate
worker: celery worker --app=project.celery
web: newrelic-admin run-program gunicorn project.wsgi --log-file -
