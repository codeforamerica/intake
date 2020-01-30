install:
	pip install -r requirements/dev.txt
	npm install


serve:
	./manage.py runserver


ifeq ($(SCOPE),)
SCOPE = clips user_accounts intake formation health_check phone partnerships
endif

test:
	./manage.py test $(SCOPE) \
		--verbosity 2
	pycodestyle


test.keepdb:
	./manage.py test $(SCOPE) \
		--verbosity 2 --keepdb


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


FEATURES=features

test.behave:
	./manage.py behave $(FEATURES) \
		--keepdb


test.behave.debug:
	./manage.py behave $(FEATURES) \
		--keepdb --verbosity 2 \
		-D BEHAVE_DEBUG_ON_ERROR=yes


test.everything:
	make test.coverage.keepdb
	make test.behave
	pycodestyle



db.seed:
	python ./manage.py new_fixtures


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


# static.dev runs sass to convert .scss stylesheets to css
# it will watch the scss directory and automatically regenerate css
static.dev:
	sass --watch intake/static/intake/scss:intake/static/intake/css
