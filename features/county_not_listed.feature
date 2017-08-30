Feature: Applicants can apply for help in counties where we don't have partners
  As an applicant, I should be able to tell CMR when the county I need isn't
  listed, so that they can send me information about how to apply in all the
  places I need to clear my record.


  Scenario: Applicant can apply for two counties that aren't listed
    Given that "/apply/" loads
     When the "counties" checkbox option "not_listed" is clicked
      And submit button in form "county_form" is clicked
     Then it should load "/application/"
      And "application_county_list" should say "You are applying for help in counties where we don't have official partners"
     When applicant fills out county not listed form fields
      And the "unlisted_counties" text input is set to "Delta Quadrant, Narnia County"
      And submit button in form "county_form" is clicked
     Then it should load "/thanks/"
      And "next_steps" should say "We will contact you in the next week with information on how to clear your record in Delta Quadrant, Narnia County"

  Scenario: Applicant can apply for an unlisted county along with a listed one
    Given that "/apply/" loads
     When the "counties" checkbox option "not_listed" is clicked
      And the "counties" checkbox option "contracosta" is clicked
      And submit button in form "county_form" is clicked
     Then it should load "/application/"
      And "application_county_list" should say "You are applying for help in Contra Costa and counties where we don't have official partners."
     When applicant fills out a county application form with basic answers
      And applicant fills out additional fields for Contra Costa
      And the "unlisted_counties" text input is set to "Delta Quadrant, Narnia County"
      And submit button in form "county_form" is clicked
     Then it should load "/thanks/"
      And "next_steps" should say "We will contact you in the next week with information on how to clear your record in Delta Quadrant, Narnia County"

  # Scenario: CfA staff gets reminders and can view 'not-listed' apps
