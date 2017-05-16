from django.views.generic.base import TemplateView
from intake.services import statistics


class Stats(TemplateView):
    """A view that shows a public summary of service performance.
    """
    template_name = "stats.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {'org_stats': statistics.get_org_data_dict()}
        return context


stats = Stats.as_view()
