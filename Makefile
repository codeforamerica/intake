
install:
	pip install -r requirements/dev.txt

serve:
	./manage.py runserver

test:
	coverage run \
		--source='./project/','./intake/' \
		--omit='./project/settings/prod.py','./project/wsgi.py' \
		./manage.py test tests.integration
	coverage report

test.functional:
	python ./manage.py test tests.functional