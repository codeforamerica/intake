from django.db import models
from django.contrib.auth.models import User
import user_accounts
from user_accounts import exceptions
import uuid
import intake.services.events_service as EventsService


class UserProfile(models.Model):
    name = models.CharField(max_length=200, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='profile')
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.PROTECT,
        related_name='profiles'
    )
    should_get_notifications = models.BooleanField(default=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    def get_display_name(self):
        name_display = self.name or self.user.email
        return "{} at {}".format(
            name_display, self.organization.name)

    def get_uuid(self):
        return self.uuid.hex

    def __str__(self):
        display = self.get_display_name()
        display += ", {}".format(self.user.email)
        if self.should_get_notifications:
            self.user.email
            display += " (gets notifications)"
        return display

    @classmethod
    def create_from_invited_user(cls, user, invitation=None, **kwargs):
        """
        This assumes we have a saved user and an
        accepted invite for that user's email
        """
        if not invitation:
            invitations = user_accounts.models.Invitation.objects.filter(
                email=user.email, accepted=True
            )
            invitation = invitations.first()
        if not invitation:
            raise exceptions.MissingInvitationError(
                "No invitation found for {}".format(user.email))
        profile = cls(
            user=user,
            organization=invitation.organization,
            should_get_notifications=invitation.should_get_notifications,
            **kwargs
        )
        profile.save()
        user.groups.add(*invitation.groups.all())
        return profile

    def get_submission_display_form(self):
        """Returns a form class appropriate for displaying
        submission data to this user.
        For now, this is based on the default form for the organization
        """
        return self.organization.get_display_form()

    def should_see_pdf(self):
        """This should be based on whether or not this user's org has a pdf
        """
        return self.organization.has_a_pdf() or self.user.is_staff

    def should_have_access_to(self, resource):
        """Returns True if user is staff or shares one org with resource

        Raises an error for resources that don't have an `organization` or
        `organizations` attribute.
        """
        if self.user.is_staff:
            return True
        if hasattr(resource, 'organization'):
            return self.organization == resource.organization
        elif hasattr(resource, 'organizations'):
            return bool(resource.organizations.filter(
                pk=self.organization_id).count())
        msg = "`{}` doesn't have a way to define UserProfile access"
        raise exceptions.UndefinedResourceAccessError(
            msg.format(resource))

    def filter_submissions(self, submissions_qset):
        if self.user.is_staff:
            return submissions_qset
        return submissions_qset.filter(organizations__profiles=self)


def get_user_display(user):
    return user.profile.get_display_name()
