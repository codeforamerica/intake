from django.db import models
from django.db.models import Case, When, BooleanField, Q
from django.conf import settings
from formation import field_types


class PurgedCounty(models.Model):
    """Placeholder for custom VIEW see intake migration 0067
    """
    class Meta:
        db_table = 'purged\".\"intake_county'
        managed = False


has_a_live_org = Q(organizations__is_live=True)
is_not_listed_county = Q(slug='not_listed')


class CountyManager(models.Manager):
    all_counties_cache = None
    all_counties_choice_list_cache = None

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)

    def get_county_choices_query(self):
        if settings.ONLY_SHOW_LIVE_COUNTIES:
            return self.order_by_name_or_not_listed().filter(
                    has_a_live_org
            ).exclude(is_not_listed_county).distinct()
        else:
            return self.order_by_name_or_not_listed(
                ).exclude(is_not_listed_county)

    def get_county_choices(self):
        if self.all_counties_cache is None:
            qset = self.get_county_choices_query()
            self.all_counties_cache = tuple((obj.slug, obj) for obj in qset)
        return self.all_counties_cache

    def get_all_counties_as_choice_list(self):
        if self.all_counties_choice_list_cache is None:
            self.all_counties_choice_list_cache = tuple(
                (obj.slug, obj) for obj in self.order_by_name_or_not_listed())

        return self.all_counties_choice_list_cache

    def annotate_is_not_listed(self):
        return self.annotate(
            is_not_listed=Case(
                            When(slug='not_listed', then=True),
                            default=False,
                            output_field=BooleanField()))

    def order_by_name_or_not_listed(self):
        return self.annotate_is_not_listed().order_by('is_not_listed', 'name')


class County(models.Model):
    objects = CountyManager()

    slug = models.SlugField()
    name = models.TextField()
    description = models.TextField()

    def get_receiving_agency(self):
        """Returns the appropriate receiving agency
        for this county. Currently there is only one per county,
        but in the future this can be used to make eligibility
        determinations
        """
        return self.organizations.filter(is_receiving_agency=True).first()

    def get_visible_organizations(self):
        return self.organizations.get_visible_set()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return str(self.name)

    def natural_key(self):
        return (self.slug, )
