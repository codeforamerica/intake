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
     When applicant fills out a county application form with basic answers
     And the "income_source" text input is set to "a job"
     And submit button in form "county_form" is clicked
     Then it should load "thanks/"
      And it should load css
      And "next_step" should say "Contra Costa County"
  Scenario: User Successfully applies to San Francisco
    Given that "apply/" loads
      And it loads css
     When the "counties" checkbox option "sanfrancisco" is clicked
      And the "confirm_county_selection" checkbox option "yes" is clicked
      And submit button in form "county_form" is clicked
     Then it should load "application/"
      And it should load css
      And "application_county_list" should say "You are applying for help in San Francisco County."
     When applicant fills out a county application form with basic answers
      And the "ssn" text input is set to "123-45-6789"
      And submit button in form "county_form" is clicked
     Then it should load "thanks/"
      And it should load css
      And "next_step" should say "San Francisco"
      And it should have a FilledPDF


