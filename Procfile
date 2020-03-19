release: python manage.py migrate
worker: celery worker --app=project.celery --concurrency=2 -E --loglevel=INFO --without-gossip --without-mingle --without-heartbeat
web: gunicorn project.heroku_wsgi --log-file=-
clock: celery beat --app=project.celery -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler