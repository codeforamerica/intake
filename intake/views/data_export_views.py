import pandas
from rest_pandas import PandasView
from rest_pandas.renderers import PandasCSVRenderer
from intake.serializers.application_serializers import \
    ApplicationCSVDownloadSerializer
from intake import models


class CSVDownloadView(PandasView):
    serializer_class = ApplicationCSVDownloadSerializer
    renderer_classes = [PandasCSVRenderer]

    def get_queryset(self, *args, **kwargs):
        return models.Application.objects.filter(
            organization__profiles__user=self.request.user)

    def get_data(self, request, *args, **kwargs):
        return pandas.to_csv('applications.csv')


csv_download = CSVDownloadView.as_view()
