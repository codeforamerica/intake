Feature: User can Apply to CMR
  Scenario: User Successfully applies to Solano
    Given that "/apply/" loads
      And it loads css
     When the "counties" checkbox option "solano" is clicked
      And submit button in form "county_form" is clicked
     Then it should load "/application/"
      And it should load css
      And "application_county_list" should say "You are applying for help in Solano."
     When applicant fills out a county application form with basic answers
      And applicant fills out additional fields for Solano
      And submit button in form "county_form" is clicked
     Then it should load "/review/"
      And it should load css
      And it displays basic answers
      And "action-forward" should say "Finish Application"
    When I click "button.action-forward"
    Then it should load "/thanks/"
      And it should load css
      And "next_step" should say "Solano"

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
      And "action-forward" should say "Finish Application"
    When I click "button.action-forward"
     Then it should load "/thanks/"
      And it should load css
      And "next_step" should say "San Francisco"
      And it should have a FilledPDF

  Scenario: User Successfully applies to Solano after fixing an error
    Given that "/apply/" loads
     When the "counties" checkbox option "solano" is clicked
      And submit button in form "county_form" is clicked
     Then it should load "/application/"
      And "application_county_list" should say "You are applying for help in Solano"
     When applicant fills out a county application form with basic answers
      And applicant fills out additional fields for Solano
      And submit button in form "county_form" is clicked
     Then it should load "/review/"
      And it displays basic answers
      And "action-forward" should say "Finish Application"
    When I click "a#edit-first_name"
    Then it should load "/application/?editing=first_name#first_name"
      And "application_county_list" should say "You are applying for help in Solano"
      And "flash_messages" should say "You can edit your answers to any questions on this page, if you need to"
      And "first_name" should say "You wanted to edit your answer to this question"
    When the "first_name" text input is set to "Joan"
      And submit button in form "county_form" is clicked
    Then it should load "/review"
      And it displays basic answers for "Joan Doe"
      And "action-forward" should say "Finish Application"
    When I click "button.action-forward"
    Then it should load "/thanks/"
      And "next_step" should say "Solano"
