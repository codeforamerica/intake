from faker import Factory as FakerFactory
from pytz import timezone
from user_accounts import models
from django.contrib.auth import models as auth_models
from django.utils.text import slugify
from django.core.management import call_command
from django.conf import settings
from user_accounts.tests.factories import profile_for_org_and_group_names

fake = FakerFactory.create('en_US')

fake_password = settings.TEST_USER_PASSWORD

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


def create_user(user=None, **attributes):
    name = attributes.get('name', fake.name())
    first_name = attributes.get('first_name', fake.first_name())
    last_name = attributes.get('last_name', fake.last_name())
    username = attributes.get('username', slugify(name))
    email = attributes.get('email',
                           username + '@' + fake.free_email_domain())
    password = fake_password
    if user:
        attributes.pop('password')
        for attr, value in attributes.iteritems():
            setattr(user, attr, value)
        user.set_password(password)
        user.save()
    else:
        user = auth_models.User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password
        )
    return user


def cfa_superuser():
    cfa = models.Organization.objects.get(slug='cfa')
    return profile_for_org_and_group_names(
        cfa, group_names=[
            'application_reviewers', 'followup_staff'],
        should_get_notifications=False,
        first_name='Fake', last_name='CFA',
        is_staff=True, is_superuser=True)


def cfa_monitor_user():
    cfa = models.Organization.objects.get(slug='cfa')
    return profile_for_org_and_group_names(
        cfa, group_names=['performance_monitors'],
        should_get_notifications=False,
        username='monitor_user')


def for_all_receiving_orgs():
    return [
        profile_for_org_and_group_names(
            org, group_names=['application_reviewers'],
            should_get_notifications=True)
        for org in models.Organization.objects.filter(is_receiving_agency=True)
    ]


def create_seed_users():
    for_all_receiving_orgs()
    cfa_superuser()
    cfa_monitor_user()


def serialize_seed_users():
    call_command(
        'dumpdata', 'auth.User', 'user_accounts.UserProfile',
        use_natural_primary_keys=True,
        use_natural_foreign_keys=True,
        indent=2,
        output='user_accounts/fixtures/mock_profiles.json')


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
            username = '{}_user_{}'.format(org.slug, i)
            profile = profile_for_org_and_group_names(
                org, should_get_notifications=org.is_receiving_agency,
                username=username)
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
