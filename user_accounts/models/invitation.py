
from django.db import models
from invitations.models import Invitation as BaseInvitation
from django.utils.crypto import get_random_string
from collections import namedtuple
from allauth.account.adapter import get_adapter
from allauth.account import utils as allauth_account_utils

import user_accounts


class Invitation(BaseInvitation):
    organization = models.ForeignKey(
        'user_accounts.Organization',
        on_delete=models.CASCADE
    )
    groups = models.ManyToManyField(
        'auth.Group', related_name='invitations')
    should_get_notifications = models.BooleanField(default=False)
    # inherits the following fields
    #   email
    #   accepted
    #   created
    #   key
    #   sent
    #   inviter
    #   objects

    @classmethod
    def create(cls, email, organization, inviter=None, **kwargs):
        key = get_random_string(64).lower()
        return cls._default_manager.create(
            email=email,
            organization=organization,
            key=key,
            inviter=inviter,
            **kwargs
        )

    def create_user_from_invite(self, password=None, accept=True, **kwargs):
        '''This is a utility function that
        creates a new user, with an associated profile and organization,
        from an existing invite.
        It should be used to programmatically create users, similar to
        django.contrib.auth.models.UserManager.create_user()
        If no password is supplied, this will assign an unusable password
        to the user.
        This method adapts steps from:
            allauth.account.forms.SignUpForm.save()
            allauth.account.forms.SignUpForm.save.adapter.save_user()
            user_accounts.forms.SignUpForm.custom_signup()
            allauth.account.utils.setup_user_email()
        This will mark the invite as accepted, or as designated in the
        `accept` option.
        '''
        if accept:
            self.accepted = True
            self.save()
        # get the right adapter
        allauth_adapter = get_adapter()
        MockRequest = namedtuple('MockRequest', 'session')
        mock_request = MockRequest(session={})
        # get an empty instance of designated U ser model
        user = allauth_adapter.new_user(request=mock_request)
        data = dict(email=self.email)
        if password:
            data['password1'] = password
        MockForm = namedtuple('MockForm', 'cleaned_data')
        user = allauth_adapter.save_user(
            request=mock_request,
            user=user,
            form=MockForm(cleaned_data=data)
        )
        user.groups.add(*self.groups)
        user_accounts.models.UserProfile.create_from_invited_user(
            user, self, **kwargs)
        allauth_account_utils.setup_user_email(mock_request, user, [])
        return user
