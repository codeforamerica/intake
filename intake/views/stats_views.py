from django.views.generic.base import TemplateView

from intake import (
    models, serializers, constants, aggregate_serializers,
    permissions
)


def is_valid_app(app):
    for key in ('started', 'finished'):
        if app.get(key):
            return True
    return False


def all_app_orgs_are_live(app):
    return all([
        org.get('is_live', False)
        for org in app.get('organizations', [])])


def get_serialized_applications():
    apps = models.Applicant.objects.prefetch_related(
        'form_submissions',
        'form_submissions__organizations',
        'events')
    return serializers.ApplicantSerializer(apps, many=True).data


def breakup_apps_by_org(apps):
    org_buckets = {
        constants.Organizations.ALL: {
            'org': {
                'slug': constants.Organizations.ALL,
                'name': 'Total (All Organizations)'
            },
            'apps': []
        }
    }
    for app in apps:
        if is_valid_app(app) and all_app_orgs_are_live(app):
            org_buckets[constants.Organizations.ALL]['apps'].append(app)
            for org in app.get('organizations', []):
                slug = org['slug']
                if slug not in org_buckets:
                    org_buckets[slug] = {
                        'org': org,
                        'apps': []
                    }
                org_buckets[slug]['apps'].append(app)
    return list(org_buckets.values())


def organization_index(serialized_org):
    return constants.DEFAULT_ORGANIZATION_ORDER.index(
        serialized_org['org']['slug'])


def add_stats_for_org(org_data, Serializer):
    results = Serializer(org_data).data
    org_data.update(results)
    org_data.pop('apps')
    return org_data


class Stats(TemplateView):
    """A view that shows a public summary of service performance.
    """
    template_name = "stats.jinja"

    def get_context_data(self, **kwargs):
        show_private_data = self.request.user.has_perm(
            permissions.CAN_SEE_APP_STATS.app_code)
        context = super().get_context_data(**kwargs)
        all_apps = get_serialized_applications()
        apps_by_org = breakup_apps_by_org(all_apps)
        apps_by_org.sort(key=organization_index)
        Serializer = aggregate_serializers.PublicStatsSerializer
        if show_private_data:
            Serializer = aggregate_serializers.PrivateStatsSerializer
        for org_data in apps_by_org:
            add_stats_for_org(org_data, Serializer)
        context['stats'] = {'org_stats': apps_by_org}
        context['show_private_data'] = show_private_data
        return context


stats = Stats.as_view()
