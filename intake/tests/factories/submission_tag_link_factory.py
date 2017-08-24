import factory
from intake import models
from user_accounts.tests.factories import UserFactory
from .tag_factory import TagFactory
from .form_submission_factory import FormSubmissionFactory


class SubmissionTagLinkFactory(factory.DjangoModelFactory):
    content_object = factory.SubFactory(FormSubmissionFactory)
    tag = factory.SubFactory(TagFactory)
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = models.SubmissionTagLink
