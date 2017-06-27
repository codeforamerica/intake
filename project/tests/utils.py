from django.conf import settings


def login(client, profile):
    client.login(
        username=profile.user.username,
        password=settings.TEST_USER_PASSWORD)
