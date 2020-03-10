release: python manage.py migrate
worker: celery worker --app=project.celery --concurrency=2 -E --loglevel=INFO --without-gossip --without-mingle --without-heartbeat
web: gunicorn project.heroku_wsgi --log-file=-
