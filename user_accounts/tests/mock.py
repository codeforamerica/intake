import factory
from faker import Factory as FakerFactory
from pytz import timezone
from user_accounts import models
from django.contrib.auth import models as auth_models
from django.utils.text import slugify


fake = FakerFactory.create('en_US')

fake_password = 's0m3th1ng'
Pacific = timezone('US/Pacific')

def fake_superuser(**kwargs):
    username = fake.user_name()
    email = username + '@' + fake.free_email_domain()
    data = dict(username=username, email=email,
        password=fake_password)
    data.update(kwargs)
    return auth_models.User.objects.create_superuser(
        **data
        )

def fake_user_data(**kwargs):
    name = fake.name()
    email = slugify(name) + '@' + fake.free_email_domain()
    data = dict(name=name, email=email,
        password=fake_password )
    data.update(kwargs)
    return data

class OrganizationFactory(factory.DjangoModelFactory):
    name = factory.LazyFunction(fake.company)
    class Meta:
        model = models.Organization


def fake_invitation(organization, inviter, **kwargs):
    data = dict(
        email=fake.free_email(),
        created=Pacific.localize(
            fake.date_time_between('-1w', 'now'))
        )
    data.update(kwargs)
    return models.Invitation.create(
        organization=organization,
        inviter=inviter,
        **data)
