
install:
	pip install -r requirements/dev.txt

serve:
	gulp

SCOPE=tests.integration user_accounts.tests.integration
test:
	./manage.py test $(SCOPE) \
		--verbosity 2

test.coverage:
	coverage run \
		./manage.py test $(SCOPE) \
		--verbosity 2
	coverage report

test.acceptance:
	python ./manage.py test tests.acceptance

deploy.demo:
	git push demo master

deploy.prod:
	git push prod master