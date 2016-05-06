
install:
	pip install -r requirements/dev.txt

serve:
	gulp

test:
	coverage run \
		--source='./project/','./intake/' \
		--omit='./project/settings/prod.py','./project/wsgi.py' \
		./manage.py test tests.integration
	coverage report

test.functional:
	python ./manage.py test tests.functional

deploy.demo:
	gulp build
	git push demo master

deploy.prod:
	gulp build
	git push prod master