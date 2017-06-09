import factory
from intake import models


class FilledPDFFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.FilledPDF
