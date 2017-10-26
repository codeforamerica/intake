# -*- coding: utf-8 -*-

from django.db import migrations


def delete_oakland_clean_slate_clinic(apps, schema_editor):
    Address = apps.get_model('user_accounts', 'Address')
    Address.objects.filter(name='Oakland Clean Slate Walk-in Clinic',
                           organization__slug='a_pubdef').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('user_accounts', '0026_remove_hayward_clean_slate_clinic_from_addresses'),
    ]

    operations = [
        migrations.RunPython(delete_oakland_clean_slate_clinic)
    ]
