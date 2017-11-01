from zappa.async import task


@task
def create_mailgun_route(user_profile_id):
    from intake.services.mailgun_api_service import set_route_for_user_profile
    from user_accounts.models import UserProfile
    # TODO: Fix whatever is causing circular imports.
    profile = UserProfile.objects.get(pk=user_profile_id)
    set_route_for_user_profile(profile)
