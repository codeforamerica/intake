import intake.services.counties as CountiesService


class GlobalTemplateContextMixin:

    def get_context_data(self):
        counties, orgs = CountiesService.get_live_counties_and_orgs()
        return dict(
            counties=counties,
            all_county_names='counties throughout California',
            organizations=orgs
        )
