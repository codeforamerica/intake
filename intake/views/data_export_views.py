import pandas
from rest_pandas import PandasView
from rest_pandas.renderers import PandasCSVRenderer
from intake.serializers.application_serializers import \
    ApplicationCSVDownloadSerializer
from intake.services.applications_service import \
    get_all_applications_for_users_org


class CSVDownloadView(PandasView):
    serializer_class = ApplicationCSVDownloadSerializer
    renderer_classes = [PandasCSVRenderer]

    def get_queryset(self, *args, **kwargs):
        return get_all_applications_for_users_org(self.request.user)

    def get_data(self, request, *args, **kwargs):
        return pandas.to_csv('applications.csv')


csv_download = CSVDownloadView.as_view()
