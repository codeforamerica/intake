from intake.models import FillablePDF
from user_accounts.models import UserProfile

from formation.forms import county_form_selector, display_form_selector


class Organization:
    name = ""
    slug = ""
    description = ""
    is_receiving_agency = False
    county = None
    website = ""
    blurb = ""
    requires_rap_sheet = False
    address = ""
    phone_number = ""
    email = ""

    @classmethod
    def has_a_pdf(cls):
        return FillablePDF.objects.filter(
            organization=cls.slug).count() > 0

    @classmethod
    def get_referral_emails(cls):
        UserProfile.objects.filter(
            organization=cls.slug,
            should_get_notifications)

    @classmethod
    def get_default_form(cls, display=False):
        """Get the basic input form for this organization
        For the time being, this is purely based on the county
        """
        form_selector = display_form_selector if display else county_form_selector
        return form_selector.get_combined_form_class(counties=[cls.county.slug])

    @classmethod
    def get_display_form(cls):
        return cls.get_default_form(display=True)