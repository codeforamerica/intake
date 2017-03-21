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


def create_user(**attributes):
    name = attributes.get('name', fake.name())
    first_name = attributes.get('first_name', fake.first_name())
    last_name = attributes.get('last_name', fake.last_name())
    username = attributes.get('username', slugify(name))
    email = attributes.get('email',
                           username + '@' + fake.free_email_domain())
    password = fake_password
    return auth_models.User.objects.create_user(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        password=password
    )


def create_user_with_profile(organization, **attributes):
    name = attributes.pop('name', fake.name())
    user = create_user(name=name, **attributes)
    return models.UserProfile.objects.create(
        name=name,
        user=user,
        organization=organization,
    )


def create_seed_users():
    user_args = {}
    application_reviewers_group = auth_models.Group.objects.get(
        name='application_reviewers')
    for org in models.Organization.objects.filter(is_receiving_agency=True):
        username = org.slug + "_user"
        first_name = 'Fake'
        last_name = ' '.join([
            piece.title() for piece in org.slug.split('_')])
        name = ' '.join([first_name, last_name])
        email = 'bgolder+demo+{}@codeforamerica.org'.format(username)
        password = fake_password
        user_args[username] = dict(
            organization=org,
            username=username,
            first_name=first_name,
            last_name=last_name,
            name=name,
            email=email,
            password=password)
    for username, kwargs in user_args.items():
        user = auth_models.User.objects.filter(username=username).first()
        if not user:
            user = create_user(**kwargs)
        if not hasattr(user, 'profile'):
            models.UserProfile.objects.create(
                organization=kwargs['organization'],
                name=kwargs['name'],
                user=user,
                should_get_notifications=True)
        application_reviewers_group.user_set.add(user)


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
        'sfpubdef_users': [
            p.user for p in profiles if p.organization == sfpubdef],
        'ccpubdef_users': [
            p.user for p in profiles if p.organization == ccpubdef],
        'notified_users': [
            p.user for p in profiles if p.should_get_notifications],
        'agency_users': [
            p.user for p in profiles if p.organization.is_receiving_agency],
        'non_agency_users': [
            p.user for p in profiles
            if not p.organization.is_receiving_agency],
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
