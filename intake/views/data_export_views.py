import pandas
from rest_pandas import PandasView
from rest_pandas.renderers import PandasExcelRenderer
from intake.serializers.application_serializers import \
    ApplicationExcelDownloadSerializer
from intake import models


class ExcelDownloadView(PandasView):
    serializer_class = ApplicationExcelDownloadSerializer
    template_name = 'excel-download.jinja'
    renderer_classes = [PandasExcelRenderer]

    def get_queryset(self, *args, **kwargs):
        return models.Application.objects.filter(
            organization__profiles__user=self.request.user)

    def get_data(self, request, *args, **kwargs):
        return pandas.to_excel('applications.xls')
