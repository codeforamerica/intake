import factory
from intake import models


class VisitorFactory(factory.DjangoModelFactory):
    source = 'share'
    referrer = 'http://bajoradefender.org/services/clean-slate/'
    ip_address = '48.104.186.127'

    class Meta:
        model = models.Visitor
