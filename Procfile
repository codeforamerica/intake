release: python manage.py heroku_release
worker: NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program celery worker --app=project.celery --concurrency=2 -E --loglevel=INFO --without-gossip --without-mingle --without-heartbeat
web: NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program gunicorn project.heroku_wsgi --log-file=-
clock: celery beat --app=project.celery -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler