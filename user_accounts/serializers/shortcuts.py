from .user_serializer import UserMixpanelSerializer


def mixpanel_user_data(user):
    return UserMixpanelSerializer(user).data
