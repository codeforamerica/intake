import factory
import random
from faker import Factory as FakerFactory
from pytz import timezone
from user_accounts import models
from django.contrib.auth import models as auth_models
from django.utils.text import slugify


fake = FakerFactory.create('en_US')

fake_password = 'cmr-demo'
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
                password=fake_password)
    data.update(kwargs)
    return data


class PrepopulatedModelFactory:

    def __init__(self, model):
        self.model = model
        self.row_count = None

    def ensure_county_count(self):
        self.objects = list(self.model.objects.all())
        self.row_count = len(self.objects)
        if not self.row_count:
            raise Exception(
                "`{}` table is not yet populated.".format(self.model.__name__))

    def choice(self):
        self.ensure_county_count()
        return random.choice(self.objects)

    def sample(self, size=None, zero_is_okay=False):
        self.ensure_county_count()
        if not size:
            lower_limit = 0 if zero_is_okay else 1
            size = random.randint(lower_limit, self.row_count)
        return random.sample(self.objects, size)

OrganizationFactory = PrepopulatedModelFactory(models.Organization)


def create_user(**attributes):
    name = attributes.get('name', fake.name())
    username = attributes.get('username', slugify(name))
    email = attributes.get('email',
                           username + '@' + fake.free_email_domain())
    password = fake_password
    return auth_models.User.objects.create_user(
        username=username,
        email=email,
        password=password
    )


def create_user_with_profile(organization, **attributes):
    name = attributes.get('name', fake.name())
    user = create_user(name=name, **attributes)
    return models.UserProfile.objects.create(
        name=name,
        user=user,
        organization=organization,
        **attributes
    )


def create_fake_auth_models(num_users_per_org=2):
    profiles = []
    orgs = models.Organization.objects.all()
    for org in orgs:
        if org.name == "San Francisco Public Defender":
            sfpubdef = org
        elif org.name == "Contra Costa Public Defender":
            ccpubdef = org
        elif org.name == "Code for America":
            cfa = org
    for org in [sfpubdef, ccpubdef, cfa]:
        for i in range(num_users_per_org):
            profile = create_user_with_profile(
                organization=org,
                should_get_notifications=org.is_receiving_agency)
            profiles.append(profile)
    return {
        'sfpubdef': sfpubdef,
        'ccpubdef': ccpubdef,
        'cfa': cfa,
        'organizations': orgs,
        'users': [p.user for p in profiles],
        'cfa_users': [p.user for p in profiles if p.organization == cfa],
        'sfpubdef_users': [p.user for p in profiles if p.organization == sfpubdef],
        'ccpubdef_users': [p.user for p in profiles if p.organization == ccpubdef],
        'notified_users': [p.user for p in profiles if p.should_get_notifications],
        'agency_users': [p.user for p in profiles if p.organization.is_receiving_agency],
        'non_agency_users': [p.user for p in profiles if not p.organization.is_receiving_agency],
        'profiles': profiles
    }


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
