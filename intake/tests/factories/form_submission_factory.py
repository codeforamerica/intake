import factory
import faker
import random
from intake import models, constants
from intake.tests.mock_org_answers import get_answers_for_orgs
from .applicant_factory import ApplicantFactory
from user_accounts.tests.factories import ExistingOrganizationFactory

fake = faker.Factory.create(
    'en_US', includes=['intake.tests.mock_county_forms'])


class FormSubmissionFactory(factory.DjangoModelFactory):
    """This should create answers and attributes
    """
    answers = factory.LazyFunction(
        lambda: fake.cleaned_sf_county_form_answers())
    applicant = factory.SubFactory(ApplicantFactory)
    date_received = factory.LazyFunction(
        lambda: constants.PACIFIC_TIME.localize(
            fake.date_time_between('-2w', 'now')))

    class Meta:
        model = models.FormSubmission

    @classmethod
    def create(cls, *args, **kwargs):
        submission = super().create(*args, **kwargs)
        # set search fields based on answers
        updated = False
        for attr_key in models.FormSubmission.answer_fields:
            if attr_key not in kwargs:
                if attr_key in submission.answers:
                    value = submission.answers[attr_key]
                    setattr(submission, attr_key, value)
                    updated = True
                address = submission.answers.get('address', {})
                for attr_key in address:
                    value = submission.answers['address'][attr_key]
                    setattr(submission, attr_key, value)
                    updated = True
        if updated:
            submission.save()
        return submission


class FormSubmissionWithOrgsFactory(FormSubmissionFactory):
    """
    This should set answers based on the input organizations
    """

    @factory.post_generation
    def organizations(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.organizations.add_orgs_to_sub(*[
                organization for organization in extracted
            ])

    @classmethod
    def create(cls, *args, **kwargs):
        if 'organizations' not in kwargs:
            kwargs['organizations'] = ExistingOrganizationFactory.sample(
                random.randint(1, 3))
        # set answers based on the designated organizations
        if 'answers' not in kwargs:
            kwargs['answers'] = get_answers_for_orgs(kwargs['organizations'])
        submission = super().create(*args, **kwargs)
        # adjust created and updated dates of applications to match
        # the form submission's faked date
        for app in submission.applications.all():
            app.created = submission.date_received
            app.save()
        return submission
