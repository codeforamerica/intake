release: python manage.py heroku_release
worker: newrelic-admin run-program celery worker --app=project.celery --concurrency=2 -E --loglevel=INFO --without-gossip --without-mingle --without-heartbeat
web: newrelic-admin run-program gunicorn project.heroku_wsgi --log-file=-
