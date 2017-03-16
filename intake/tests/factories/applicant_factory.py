import factory
from intake import models
from .visitor_factory import VisitorFactory


class ApplicantFactory(factory.DjangoModelFactory):
    visitor = factory.SubFactory(VisitorFactory)

    class Meta:
        model = models.Applicant
