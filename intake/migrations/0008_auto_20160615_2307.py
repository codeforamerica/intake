# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-15 23:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('intake', '0007_auto_20160615_1954'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicationlogentry',
            name='time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='formsubmission',
            name='date_received',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
