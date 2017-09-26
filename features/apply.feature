Feature: User can Apply to CMR
  Scenario: User Successfully applies to Contra Costa
    Given that "/apply/" loads
      And it loads css
     When the "counties" checkbox option "contracosta" is clicked
      And submit button in form "county_form" is clicked
     Then it should load "/application/"
      And it should load css
      And "application_county_list" should say "You are applying for help in Contra Costa."
     When applicant fills out a county application form with basic answers
      And applicant fills out additional fields for Contra Costa
      And submit button in form "county_form" is clicked
     Then it should load "/review/"
      And it should load css
      And it displays basic answers
    When I click "button.action-forward"
    Then it should load "/thanks/"
      And it should load css
      And "next_step" should say "Contra Costa"
  Scenario: User Successfully applies to San Francisco
    Given a fillable PDF for "sf_pubdef"
      And that "/apply/" loads
      And it loads css
     When the "counties" checkbox option "sanfrancisco" is clicked
      And submit button in form "county_form" is clicked
     Then it should load "/application/"
      And it should load css
      And "application_county_list" should say "You are applying for help in San Francisco."
     When applicant fills out a county application form with basic answers
      And applicant fills out additional fields for San Francisco
      And submit button in form "county_form" is clicked
     Then it should load "/review/"
      And it should load css
      And it displays basic answers
    When I click "button.action-forward"
     Then it should load "/thanks/"
      And it should load css
      And "next_step" should say "San Francisco"
      And it should have a FilledPDF
  Scenario: User Successfully applies to Contra Costa after fixing an error
    Given that "/apply/" loads
     When the "counties" checkbox option "contracosta" is clicked
      And submit button in form "county_form" is clicked
     Then it should load "/application/"
      And "application_county_list" should say "You are applying for help in Contra Costa"
     When applicant fills out a county application form with basic answers
      And applicant fills out additional fields for Contra Costa
      And submit button in form "county_form" is clicked
     Then it should load "/review/"
      And it displays basic answers
    When I click "button.action-back"
    Then it should load "/application/"
      And "application_county_list" should say "You are applying for help in Contra Costa"
    When the "first_name" text input is set to "Joan"
      And submit button in form "county_form" is clicked
    Then it should load "/review"
      And it displays basic answers for "Joan Doe"
    When I click "button.action-forward"
    Then it should load "/thanks/"
      And "next_step" should say "Contra Costa"
