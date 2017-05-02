Feature: User can Apply to CMR
  Scenario: User Successfully applies to Contra Costa
    Given that "apply/" loads
      And it loads css
     When the "counties" checkbox option "contracosta" is clicked
      And the "confirm_county_selection" checkbox option "yes" is clicked
      And submit button in form "county_form" is clicked
     Then it should load "application/"
      And it should load css
      And "application_county_list" should say "You are applying for help in Contra Costa County."
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
      And the "income_source" text input is set to "a job"
      And "yes" is clicked on the "consent_to_represent" radio button
      And "yes" is clicked on the "understands_limits" radio button
      And the "how_did_you_hear" text input is set to "Listening"
      And the "additional_information" text input is set to "So cool"
      And submit button in form "county_form" is clicked
     Then it should load "thanks/"
      And it should load css
      And "next_step" should say "Contra Costa County"

