
install:
	pip install -r requirements/dev.txt

serve:
	python ./manage.py runserver


test:
	python ./manage.py test tests.integration


test.functional:
	python ./manage.py test tests.functional