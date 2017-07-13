import factory
from user_accounts import models
from .organization_factory import FakeOrganizationFactory
from .user_factory import UserFactory, user_with_name_and_email_from_org_slug


class UserProfileFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Fake User {}'.format(n))
    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(FakeOrganizationFactory)
    should_get_notifications = True

    class Meta:
        model = models.UserProfile


def fake_app_reviewer(**kwargs):
    user = UserFactory(group_names=['application_reviewers'], **kwargs)
    return UserProfileFactory(user=user)


def profile_for_org_and_group_names(
        org, group_names=None, should_get_notifications=True, **user_kwargs):
    """Creates a user and user profile based on the org slug

    For example, if org.slug is 'yolo_pubdef':
        user.username == 'yolo_pubdef_user'
        user.first_name == 'Fake'
        user.last_name == 'Yolo Pubdef User'
        profile.name == 'Fake Yolo Pubdef User'
        email = bgolder+demo+yolo_pubdef_user@codeforamerica.org

    if a list of strings are passed through group_names, each corresponding
    group will be added.
    """
    if not group_names:
        group_names = []
    user = user_with_name_and_email_from_org_slug(
        org.slug, group_names=group_names, **user_kwargs)
    return UserProfileFactory(
        user=user, organization=org,
        name=' '.join([user.first_name, user.last_name]),
        should_get_notifications=should_get_notifications)


def profile_for_slug_in_groups(org_slug, group_names=None, **kwargs):
    return profile_for_org_and_group_names(
        models.Organization.objects.get(slug=org_slug),
        group_names=group_names, **kwargs)


def app_reviewer(org_slug=None, **kwargs):
    if org_slug:
        org = models.Organization.objects.get(slug=org_slug)
    else:
        org = FakeOrganizationFactory()
    return profile_for_org_and_group_names(
        org, ['application_reviewers'], **kwargs)


def followup_user(**kwargs):
    return profile_for_slug_in_groups(
        'cfa', group_names=['followup_staff'], is_staff=True, **kwargs)


def monitor_user(**kwargs):
    return profile_for_slug_in_groups(
        'cfa', group_names=['performance_monitors'], **kwargs)
