install:
	pip install -r requirements/dev.txt
	npm install


serve:
	gulp


SCOPE=user_accounts intake formation
test:
	./manage.py test $(SCOPE) \
		--verbosity 2


test.keepdb:
	./manage.py test $(SCOPE) \
		--verbosity 2 --keepdb

test.review_app:
	pip install -r requirements/dev.txt
	make db.seed
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


test.deluxe:
	DELUXE_TEST=1 \
	./manage.py test $(SCOPE) \
		--verbosity 2


test.acceptance:
	python ./manage.py test tests.acceptance


test.screenshots:
	python ./manage.py test \
		tests.acceptance.test_screenshots \
		--verbosity 2

deploy.feature:
	git push -f feature HEAD:master
	heroku run --app cmr-feature make db.seed

deploy.demo:
	git push -f demo HEAD:master
	heroku run --app cmr-demo make db.seed

deploy.prod:
	git push prod master
	heroku run --app cmr-prod python manage.py loaddata \
		counties \
		organizations \
		addresses \
		groups \
		template_options


db.setup:
	python ./manage.py migrate
	make db.seed


db.pull.demo:
	dropdb intake --if-exists
	heroku pg:pull --app cmr-demo DATABASE_URL intake


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

db.core_seed:
	python ./manage.py loaddata \
		counties \
		organizations \
		addresses \
		mock_profiles \
		template_options

db.seed:
	make db.core_seed
	python ./manage.py loaddata \
		mock_2_submissions_to_a_pubdef \
		mock_2_submissions_to_ebclc \
		mock_2_submissions_to_cc_pubdef \
		mock_2_submissions_to_sf_pubdef \
		mock_2_submissions_to_monterey_pubdef \
		mock_2_submissions_to_solano_pubdef \
		mock_2_submissions_to_san_diego_pubdef \
		mock_2_submissions_to_san_joaquin_pubdef \
		mock_2_submissions_to_santa_clara_pubdef \
		mock_2_submissions_to_santa_cruz_pubdef \
		mock_2_submissions_to_fresno_pubdef \
		mock_2_submissions_to_sonoma_pubdef \
		mock_2_submissions_to_tulare_pubdef \
		mock_1_submission_to_multiple_orgs \
		mock_1_bundle_to_a_pubdef \
		mock_1_bundle_to_ebclc \
		mock_1_bundle_to_sf_pubdef \
		mock_1_bundle_to_cc_pubdef \
		mock_1_bundle_to_monterey_pubdef \
		mock_1_bundle_to_solano_pubdef \
		mock_1_bundle_to_san_diego_pubdef \
		mock_1_bundle_to_san_joaquin_pubdef \
		mock_1_bundle_to_santa_clara_pubdef \
		mock_1_bundle_to_santa_cruz_pubdef \
		mock_1_bundle_to_fresno_pubdef \
		mock_1_bundle_to_sonoma_pubdef \
		mock_1_bundle_to_tulare_pubdef \
		mock_application_events


notebook:
	python ./manage.py shell_plus --notebook
