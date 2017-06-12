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
        context, applicant_name="Waldo Waldini",
        county_names="San Francisco, Contra Costa, and Yolo"):
    first_name, last_name = applicant_name.split(' ')
    counties = get_counties_from_county_names_string(county_names)
    substeps = ['Given that "apply/" loads']
    substeps.append(
        'When the "counties" checkbox option "{slug}" is clicked'.format(
            slug=counties.pop(0)))
    for county in counties:
        substeps.append(
            'And the "counties" checkbox option "{slug}" is clicked'.format(
                county.slug))
    substeps.append('''And the "confirm_county_selection" checkbox option "yes" is clicked
        And submit button in form "county_form" is clicked
        Then it should load "application/"
        When "{name}" fills out a county application form with basic answers
        '''.format(name=applicant_name))
    for county in counties:
        substeps.append(
            'And applicant fills out additional fields for {county}'.format(
                county.name))
    substeps.append('''And submit button in form "county_form" is clicked
        Then it should load "thanks/"
        '''.format(first_name=first_name, last_name=last_name))
    context.execute_steps('\n'.join(substeps))


@when('applicant fills out a county application form with basic answers')
def step_impl(context):
    context.execute_steps('''
      When the "contact_preferences" checkbox option "prefers_email" is clicked
       And the "first_name" text input is set to "Jane"
       And the "last_name" text input is set to "Doe"
       And the "phone_number" text input is set to "5105555555"
       And the "email" text input is set to "testing@codeforamerica.org"
       And the "dob.day" text input is set to "1"
       And the "dob.month" text input is set to "1"
       And the "dob.year" text input is set to "1980"
       And "yes" is clicked on the "us_citizen" radio button
       And the "address.street" text input is set to "111 Coaster HWY"
       And the "address.city" text input is set to "San Francisco"
       And the "address.state" text input is set to "CA"
       And the "address.zip" text input is set to "91011"
       And "yes" is clicked on the "on_probation_parole" radio button
       And "yes" is clicked on the "serving_sentence" radio button
       And "yes" is clicked on the "currently_employed" radio button
       And the "monthly_income" text input is set to "1000"
       And the "monthly_expenses" text input is set to "1000"
       And "yes" is clicked on the "consent_to_represent" radio button
       And "yes" is clicked on the "understands_limits" radio button
       And the "how_did_you_hear" text input is set to "Listening"
       And the "additional_information" text input is set to "So cool"
    ''')


@when('applicant fills out additional fields for Contra Costa')
def coco_fields(context):
    context.execute_steps('''
            And the "income_source" text input is set to "a job"
      ''')


@when('applicant fills out additional fields for San Francisco')
def sf_fields(context):
    context.execute_steps('''
            And the "ssn" text input is set to "123-45-6789"
      ''')


@when('applicant fills out additional fields for Yolo')
def yolo_fields(context):
    context.execute_steps('''
And the "how_much_savings" text input is set to "1000"
And the "income_source" text input is set to "a job"
And "yes" is clicked on the "owns_home" radio button
And the "how_many_dependents" text input is set to "2"
And "yes" is clicked on the "is_married" radio button
And "background_check" is clicked on the "reasons_for_applying" radio button
      ''')
