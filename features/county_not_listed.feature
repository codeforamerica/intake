Feature: Applicants can apply for help in counties where we don't have partners
  As an applicant, I should be able to tell CMR when the county I need isn't
  listed, so that they can send me information about how to apply in all the
  places I need to clear my record.


  Scenario: Applicant can apply for two counties that aren't listed
    Given that "/apply/" loads
     When the "counties" checkbox option "not_listed" is clicked
      And submit button in form "county_form" is clicked
     Then it should load "/application/"
      And "application_county_list" should be empty
        # insert each field here
      And submit button in form "county_form" is clicked
     Then it should load "/thanks/"
      And "next_step" should say "We will contact you"

  Scenario: Applicant can apply for an unlisted county along with a listed one
  Scenario: CfA staff gets reminders and can view 'not-listed' apps
