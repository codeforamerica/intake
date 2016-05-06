
install:
	pip install -r requirements/dev.txt

serve:
	gulp

test:
	coverage run \
		--source='./project/','./intake/' \
		--omit='./project/settings/prod.py','./project/wsgi.py' \
		./manage.py test tests.integration \
		--verbosity 2
	coverage report

test.functional:
	python ./manage.py test tests.functional

deploy.demo:
	git push demo master

deploy.prod:
	git push prod master