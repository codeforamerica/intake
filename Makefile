
install:
	pip install -r requirements/dev.txt

serve:
	gulp

SCOPE=tests.integration
test:
	./manage.py test $(SCOPE) \
		--verbosity 2

test.coverage:
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