from django.db import models

from intake import constants
from formation import field_types


class CountyManager(models.Manager):

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


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
        if self.slug == constants.Counties.ALAMEDA:
            # if under 3000 and not owns home
            income = answers.get('monthly_income')
            owns_home = answers.get('owns_home')
            if income < 3000 and owns_home == field_types.NO:
                # return alameda pub def
                return self.organizations.get(
                    slug=constants.Organizations.ALAMEDA_PUBDEF)
            else:
                # return ebclc
                return self.organizations.get(
                    slug=constants.Organizations.EBCLC)
            # return first receiving agency
        return self.organizations.filter(is_receiving_agency=True).first()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return str(self.name)

    def natural_key(self):
        return (self.slug, )
