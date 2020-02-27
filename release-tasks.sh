#!/bin/bash

npm install
python manage.py migrate --settings project.settings.prod
