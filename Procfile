worker: newrelic-admin run-program celery worker --app=project.celery -E --loglevel=INFO
web: newrelic-admin run-program gunicorn project.heroku_wsgi --log-file -
