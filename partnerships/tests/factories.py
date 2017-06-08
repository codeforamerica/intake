import factory
from partnerships import models
from intake.tests.factories import VisitorFactory


class PartnershipLeadFactory(factory.DjangoModelFactory):
    visitor = factory.SubFactory(VisitorFactory)
    name = 'Ziggy Stardust'
    email = 'ziggy@mars.space'
    organization_name = 'Spiders from Mars'
    message = 'Jamming good with Weird and Gilly'

    class Meta:
        model = models.PartnershipLead
