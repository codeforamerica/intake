# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-04 21:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intake', '0061_purgedformsubmission'),
    ]

    operations = [
        migrations.RunSQL(
            """CREATE OR REPLACE VIEW purged.intake_formsubmission AS
            SELECT %s From intake_formsubmission;
            """ %
            ', '.join(
                [
                    'anonymous_name',
                    "date_part('year', age(dob)) as age",
                    'contact_preferences',
                    'preferred_pronouns',
                    'state',
                    'us_citizen',
                    'is_veteran',
                    'is_student',
                    'being_charged',
                    'serving_sentence',
                    'on_probation_parole',
                    'where_probation_or_parole',
                    'when_probation_or_parole',
                    'finished_half_probation',
                    'reduced_probation',
                    'rap_outside_sf',
                    'when_where_outside_sf',
                    'has_suspended_license',
                    'owes_court_fees',
                    'currently_employed',
                    'monthly_income',
                    'income_source',
                    'on_public_benefits',
                    'owns_home',
                    'monthly_expenses',
                    'household_size',
                    'dependents',
                    'is_married',
                    'has_children',
                    'date_received',
                    'id',
                ]), "")]
