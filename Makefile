install:
	pip install -r requirements/dev.txt
	npm install


serve:
	gulp


SCOPE=user_accounts intake formation
test:
	./manage.py test $(SCOPE) \
		--verbosity 2
	pep8


test.keepdb:
	./manage.py test $(SCOPE) \
		--verbosity 2 --keepdb


test.review_app:
	pip install -r requirements/dev.txt
	./manage.py migrate --settings project.settings.review_app
	coverage run ./manage.py test $(SCOPE) \
		--settings project.settings.review_app \
		--verbosity 2 --keepdb
	coverage report -m


test.coverage:
	coverage run \
		./manage.py test $(SCOPE) \
		--verbosity 2
	coverage report -m


test.coverage.keepdb:
	coverage run \
		./manage.py test $(SCOPE) \
		--verbosity 2 --keepdb
	coverage report -m


test.deluxe:
	DELUXE_TEST=1 \
	./manage.py test $(SCOPE) \
		--verbosity 2


db.seed:
	python ./manage.py load_essential_data
	python ./manage.py load_mock_data


db.setup:
	python ./manage.py migrate
	make db.seed


db.total_rebuild:
	dropdb intake
	createdb intake
	make db.setup


db.dump_fixtures:
	python ./manage.py dumpdata \
	    auth.User \
	    user_accounts.UserProfile \
	    auth.Group \
	    -o user_accounts/fixtures/mock_profiles.json \
	    --natural-foreign --natural-primary \
	    --indent 2
	python ./manage.py dumpdata \
	    auth.Group \
	    -o user_accounts/fixtures/groups.json \
	    --natural-foreign --natural-primary \
	    --indent 2
	python ./manage.py dumpdata \
	    user_accounts.Organization \
	    -o user_accounts/fixtures/organizations.json \
	    --natural-foreign --natural-primary \
	    --indent 2
	python ./manage.py dumpdata \
	    user_accounts.Address \
	    -o user_accounts/fixtures/addresses.json \
	    --natural-foreign \
	    --indent 2
	python ./manage.py dumpdata \
	    intake.County \
	    -o intake/fixtures/counties.json \
	    --indent 2 \
	    --format json

db.pull.demo:
	dropdb intake --if-exists
	heroku pg:pull --app cmr-demo DATABASE_URL intake
