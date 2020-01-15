from django.db import models
from intake import models as intake_models
from intake.utils import coerce_to_ids
import user_accounts
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils.html import conditional_escape
from django.contrib.auth.models import User
from project.jinja2 import oxford_comma, format_phone_number


class OrganizationManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)

    def extract_sub(self):
        args, kwargs = self._constructor_args
        if len(args) == 1 and isinstance(
                args[0], intake_models.FormSubmission):
            return args[0]

    def add_orgs_to_sub(self, *orgs):
        sub = self.extract_sub()
        if sub and orgs:
            applications = [
                intake_models.Application(
                    form_submission=sub,
                    organization_id=org_id)
                for org_id in coerce_to_ids(orgs)
            ]
            intake_models.Application.objects.bulk_create(applications)

    def remove_orgs_from_sub(self, *orgs):
        sub = self.extract_sub()
        if sub and orgs:
            sub.applications.filter(organization__in=orgs).delete()

    def not_cfa(self):
        return self.exclude(slug='cfa')


class PurgedOrganization(models.Model):
    """Placeholder for custom VIEW see intake migration 0025
    """
    class Meta:
        db_table = 'purged\".\"user_accounts_organization'
        managed = False


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
    is_accepting_applications = models.BooleanField(default=True)
    is_checking_notifications = models.BooleanField(default=True)
    is_live = models.BooleanField(default=False)
    requires_rap_sheet = models.BooleanField(default=False)
    requires_declaration_letter = models.BooleanField(default=False)
    show_pdf_only = models.BooleanField(default=False)
    short_confirmation_message = models.TextField(blank=True)
    long_confirmation_message = models.TextField(blank=True)
    short_followup_message = models.TextField(blank=True)
    long_followup_message = models.TextField(blank=True)
    address = models.TextField(blank=True)
    phone_number = models.TextField(blank=True)
    fax_number = models.TextField(blank=True)
    email = models.TextField(blank=True)
    notify_on_weekends = models.BooleanField(default=False)
    can_transfer_applications = models.BooleanField(default=False)
    transfer_partners = models.ManyToManyField(
        'self', symmetrical=True, blank=True)
    needs_applicant_followups = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return str(self.name)

    def natural_key(self):
        return (self.__str__(), )

    def get_referral_emails(self):
        """Get the emails of users who get notifications for this agency.
        This is not an efficient query and assumes that profiles and
        users have been prefetched in a previous query.
        """
        emails = list(User.objects.filter(
            profile__should_get_notifications=True,
            profile__organization=self).values_list('email', flat=True))
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

    def get_absolute_url(self):
        return reverse(
            'intake-partner_detail',
            kwargs=dict(organization_slug=self.slug))

    def get_url_anchor_tag(self):
        return mark_safe('<a href="{url}">{name}</a>'.format(
            url=self.get_absolute_url(),
            name=conditional_escape(self.name)))

    def get_last_bundle(self):
        return intake_models.ApplicationBundle.objects.filter(
            organization=self).latest('id')

    def get_contact_info_message(self):
        if not (self.phone_number or self.email):
            raise ValueError("no email or phone exists for this organization")
        messages = []
        if self.phone_number:
            messages.append(
                "call {}".format(format_phone_number(self.phone_number)))
        if self.email:
            messages.append("email {}".format(self.email))
        return oxford_comma(messages, use_or=True)
