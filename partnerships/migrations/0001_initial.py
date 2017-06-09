# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-06-07 23:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('intake', '0058_replace_event_logic_with_flags'),
    ]

    operations = [
        migrations.CreateModel(
            name='PartnershipLead',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.TextField()),
                ('email', models.EmailField(max_length=254)),
                ('organization_name', models.TextField()),
                ('message', models.TextField(blank=True)),
                ('visitor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='partnership_leads', to='intake.Visitor')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
