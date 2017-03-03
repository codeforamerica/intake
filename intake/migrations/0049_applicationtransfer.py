# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-03-03 18:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('intake', '0048_template_field_validators'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicationTransfer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField(blank=True)),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming_transfer', to='intake.StatusUpdate')),
                ('origin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outgoing_transfer', to='intake.StatusUpdate')),
            ],
        ),
    ]
