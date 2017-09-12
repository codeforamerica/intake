from intake.models import Application
from user_accounts.models import Organization
from .form_submission_factory import FormSubmissionWithOrgsFactory


def make_apps_for(*org_slugs, count=3, **sub_kwargs):
    apps = []
    orgs = Organization.objects.filter(slug__in=org_slugs)
    for i in range(count):
        sub = FormSubmissionWithOrgsFactory(organizations=orgs, **sub_kwargs)
        apps.append(sub.applications.first())
    return apps


def make_app_ids_for(*org_slugs, count=3):
    return [app.id for app in make_apps_for(*org_slugs, count)]


def make_apps_for_sf(count=3):
    return make_apps_for('sf_pubdef', count=count)


def make_app_ids_for_sf(count=3):
    return make_app_ids_for('sf_pubdef', count=count)


def apps_queryset(apps):
    return Application.objects.filter(id__in=[app.id for app in apps])
