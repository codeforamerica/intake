import factory
from intake import models


class FillablePDFFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.FillablePDF
