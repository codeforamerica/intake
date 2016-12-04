from django.db import models
from intake import models as intake_models
from intake import constants
from formation.forms import county_form_selector, display_form_selector
import user_accounts
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.utils.html import conditional_escape



class OrganizationManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)


class Organization(models.Model):
    objects = OrganizationManager()
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, null=True)
    county = models.ForeignKey(intake_models.County,
                               on_delete=models.SET_NULL,
                               null=True, blank=True,
                               related_name='organizations')
    website = models.URLField(blank=True)
    blurb = models.TextField(blank=True)
    is_receiving_agency = models.BooleanField(default=False)
    requires_rap_sheet = models.BooleanField(default=False)
    requires_declaration_letter = models.BooleanField(default=False)
    show_pdf_only = models.BooleanField(default=False)
    short_confirmation_message = models.TextField(blank=True)
    long_confirmation_message = models.TextField(blank=True)
    address = models.TextField(blank=True)
    phone_number = models.TextField(blank=True)
    email = models.TextField(blank=True)
    notify_on_weekends = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)

    def natural_key(self):
        return (self.__str__(), )

    def get_transfer_org(self):
        """If this organization is allowed to transfer to another
        organization, this shoud return the other organization they are
        allowed to transfer submissions to.
        """
        if self.slug == constants.Organizations.ALAMEDA_PUBDEF:
            return self.__class__.objects.get(
                slug=constants.Organizations.EBCLC)
        elif self.slug == constants.Organizations.EBCLC:
            return self.__class__.objects.get(
                slug=constants.Organizations.ALAMEDA_PUBDEF)
        return None

    def get_referral_emails(self):
        """Get the emails of users who get notifications for this agency.
        This is not an efficient query and assumes that profiles and
        users have been prefetched in a previous query.
        """
        emails = [
            profile.user.email
            for profile
            in self.profiles.filter(should_get_notifications=True)]
        if not emails:
            # this assumes that any existing invitations are valid emails
            # to use for notification
            emails = list(user_accounts.models.Invitation.objects.filter(
                organization=self).values_list('email', flat=True))
        if not emails:
            msg = "{} has no invites or users".format(self)
            raise user_accounts.exceptions.NoEmailsForOrgError(msg)
        return emails

    def has_a_pdf(self):
        """Checks for any linked intake.models.FillablePDF objects
        """
        return self.pdfs.count() > 0

    def get_default_form(self, display=False):
        """Get the basic input form for this organization
        For the time being, this is purely based on the county
        """
        form_selector = display_form_selector \
            if display else county_form_selector
        return form_selector.get_combined_form_class(
            counties=[self.county.slug])

    def get_display_form(self):
        return self.get_default_form(display=True)

    def get_absolute_url(self):
        return reverse(
            'intake-partner_detail',
            kwargs=dict(organization_slug=self.slug))

    def get_url_anchor_tag(self):
        return mark_safe('<a href="{url}">{name}</a>'.format(
            url=self.get_absolute_url(),
            name=conditional_escape(self.name)))

    def get_unopened_apps(self):
        opened_sub_ids = intake_models.ApplicationLogEntry.objects.filter(
            event_type=intake_models.ApplicationLogEntry.OPENED,
            user__profile__organization=self,
            submission_id__isnull=False
        ).values_list('submission_id', flat=True)
        return self.submissions.all().exclude(pk__in=opened_sub_ids)

    def get_last_bundle(self):
        return intake_models.ApplicationBundle.objects.filter(
                organization=self).latest('id')
