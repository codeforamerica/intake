from django.conf import settings
from django.contrib.auth.models import User, Group
import factory


def add_groups_to_user(user, groups):
    for group in groups:
        user.groups.add(group)


class UserFactory(factory.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'fakeuser{}'.format(n))
    email = factory.Sequence(
        lambda n: 'fakeuser{}@cyber.horse'.format(n))
    password = factory.PostGenerationMethodCall(
        'set_password', settings.TEST_USER_PASSWORD)
    is_active = True

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            add_groups_to_user(self, extracted)

    @factory.post_generation
    def group_names(self, create, extracted, **kwargs):
        if create and extracted:
            groups = Group.objects.filter(name__in=list(extracted))
            add_groups_to_user(self, groups)

    class Meta:
        model = User


def user_with_name_and_email_from_org_slug(org_slug, **kwargs):
    username = kwargs.get('username', org_slug + '_user')
    default_kwargs = dict(
        username=username,
        email='bgolder+demo+{}@codeforamerica.org'.format(username),
        first_name='Fake',
        last_name=username.replace('_', ' ').title())
    default_kwargs.update(kwargs)
    return UserFactory(**default_kwargs)
