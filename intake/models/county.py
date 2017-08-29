from django.db import models
from django.db.models import Case, When

from intake import constants
from formation import field_types


class PurgedCounty(models.Model):
    """Placeholder for custom VIEW see intake migration 0067
    """
    class Meta:
        db_table = 'purged\".\"intake_county'
        managed = False


class CountyManager(models.Manager):

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)

    def get_county_choices(self):
        if True:
            return self.filter(
                organizations__is_live=True
            ).distinct().order_by_name_or_not_listed()
        else:
            return self.order_by_name_or_not_listed()

    def annotate_is_not_listed(self):
        return self.annotate(
            is_not_listed=Case(When(slug='not_listed', then=1)))

    def order_by_name_or_not_listed(self):
        return self.annotate_not_listed().order_by('is_not_listed', 'name')


class County(models.Model):
    objects = CountyManager()

    slug = models.SlugField()
    name = models.TextField()
    description = models.TextField()

    def get_receiving_agency(self, answers):
        """Returns the appropriate receiving agency
        for this county. Currently there is only one per county,
        but in the future this can be used to make eligibility
        determinations
        """
        # if alameda
        if self.slug == 'alameda':
            # if under 3000 and not owns home
            income = answers.get('monthly_income', None)
            owns_home = answers.get('owns_home')
            if income < 3000 and owns_home == field_types.NO:
                # return alameda pub def
                return self.organizations.get(slug='a_pubdef')
            else:
                # return ebclc
                return self.organizations.get('ebclc')
            # return first receiving agency
        return self.organizations.filter(is_receiving_agency=True).first()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return str(self.name)

    def natural_key(self):
        return (self.slug, )
