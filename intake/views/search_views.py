from django.http import HttpResponse
from django.views.generic.base import View, TemplateResponseMixin
from intake import serializers
from rest_framework.renderers import JSONRenderer
import intake.services.search_service as SearchService
import intake.services.submissions as SubmissionsService
import intake.services.events_service as EventsService


class SearchAPIBaseView(View):
    """A base view that:
        - only accepts POST
        - stores POST 'q' as self.query
        - renders a queryset with a serializer
    """

    def dispatch(self, request, *args, **kwargs):
        if self.user_is_okay(request.user):
            return super().dispatch(request, *args, **kwargs)
        return HttpResponse(status=403)

    def post(self, request):
        self.request = request
        self.query = request.POST.get('q', '')
        if not self.query:
            return HttpResponse(status=404)
        qset = self.get_queryset()
        data = self.serializer(qset, many=True).data
        EventsService.user_apps_searched(self)
        return self.get_response(data)


class ApplicationSearchAPIView(SearchAPIBaseView):
    """Takes in a POST with `q` querystring,
        returns a JSON of applications with 'name', 'url' attributes
    """
    serializer = serializers.ApplicationAutocompleteSerializer

    def user_is_okay(self, user):
        return user.is_authenticated

    def get_queryset(self):
        qset = SearchService.get_applications_with_query_string(
            self.query
        ).select_related('form_submission').order_by('-created')
        if not self.request.user.is_staff:
            qset = qset.filter(
                organization__profiles__user_id=self.request.user.id
            )
        return qset

    def get_response(self, data):
        json = JSONRenderer().render(data)
        return HttpResponse(json, content_type="application/json")


class FollowupSearchAPIView(SearchAPIBaseView, TemplateResponseMixin):
    """Takes in a POST with `q` querystring, returns rendered HTML rows for
    followups page results table
    """
    serializer = serializers.FormSubmissionFollowupListSerializer
    template_name = 'followup_list_rows.jinja'

    def user_is_okay(self, user):
        return user.is_staff

    def get_queryset(self):
        submissions = SubmissionsService.get_submissions_for_staff_user()
        return SearchService.filter_submissions_with_querystring(
            submissions, self.query)

    def get_response(self, data):
        """Should I render the HTML or should I return just a JSON?
        """
        return self.render_to_response({'results': data})


application_search = ApplicationSearchAPIView.as_view()
followup_search = FollowupSearchAPIView.as_view()
