from behave import when
from intake import models


def get_counties_from_county_names_string(county_names_string):
    """converts an oxford comma string of county names in to
        county model instances
    """
    county_names = []
    for chunk in county_names_string.split(', '):
        county_names.extend(
            [name.strip() for name in chunk.split(' and ')])
    return models.County.objects.filter(name__in=county_names)


@when('"{applicant_name}" applies to "{county_names}"')
def submit_app_to_counties(
        applicant_name="Waldo Waldini",
        county_names="San Francisco, Contra Costa, and Yolo"):
    counties = get_counties_from_county_names_string(county_names)
    first_name, last_name = applicant_name.split(' ')
    # make a full application
