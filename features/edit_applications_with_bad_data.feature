Feature: An org user can edit applications with bad data

  Background:
    Given an org user at "fresno_pubdef"

  Scenario: Org user can edit application that has existing bad data
    Given I log in as an org user at "fresno_pubdef"
      And a "fresno_pubdef" application to search for with bad data
      And I open the applicant's detail page
     Then "phone_number" should say "5555555555"
      And "alternate_phone_number" should say "5555555555"
      And "email" should say "waldo@odlaw"
      And "dob" should say "February/28/1972"
     # check existing data and input values on the edit page
     When I click the "Edit info" link to the applicant's edit page
     Then it should load the applicant's edit page
      And the "existing_phone_number" input value should be "5555555555"
      And the "existing_alternate_phone_number" input value should be "5555555555"
      And the "existing_email" input value should be "waldo@odlaw"
      And the "existing_dob.day" input value should be "28"
      And the "existing_dob.month" input value should be "February"
      And the "existing_dob.year" input value should be "1972"
      And the "phone_number" input value should be empty
      And the ".phone_number .errorlist" element should say "You entered '5555555555', which doesn't look like a valid phone number"
      And the "alternate_phone_number" input value should be empty
      And the ".alternate_phone_number .errorlist" element should say "You entered '5555555555', which doesn't look like a valid phone number"
      And the "email" input value should be "waldo@odlaw"
      And the ".email .errorlist" element should say "Please enter a valid email"
      And the "dob.month" input value should be empty
      And the "dob.day" input value should be "28"
      And the "dob.year" input value should be "1972"
      And the ".dob .errorlist" element should say "You entered 'February', which doesn't look like a number"
     # make one benign edit, and one still bad edit to data
     When the "first_name" text input is set to "Waldino"
      And the "email" text input is set to "waldino@odlaw"
      And submit button in form "application_edit_form" is clicked
     # check again for correct existing data and validation errors 
     Then it should load the applicant's edit page
      And the "existing_first_name" input value should be "Waldo"
      And the "existing_phone_number" input value should be "5555555555"
      And the "existing_alternate_phone_number" input value should be "5555555555"
      And the "existing_email" input value should be "waldo@odlaw"
      And the "existing_dob.day" input value should be "28"
      And the "existing_dob.month" input value should be "February"
      And the "existing_dob.year" input value should be "1972"
      And the "first_name" input value should be "Waldino"
      And the "phone_number" input value should be empty
      # And I need to debug
      And the ".phone_number .errorlist" element should say "'Text Message' is set as the preferred contact method, but you didn't enter a phone number."
      And the "alternate_phone_number" input value should be empty
      And the "email" input value should be "waldino@odlaw"
      And the ".email .errorlist" element should say "Please enter a valid email"
      And the "dob.month" input value should be empty
      And the "dob.day" input value should be "28"
      And the "dob.year" input value should be "1972"
      And the ".dob .errorlist" element should say "This field is required."
     # corrections to override validation errors
     When the "email" text input is set to "waldo@odlaw.org"
      And the "contact_preferences" checkbox option "prefers_sms" is clicked
      And the "dob.month" text input is set to "2"
      And submit button in form "application_edit_form" is clicked
     Then it should load the applicant's detail page
      # check for new values and cleared bad data
      And "first_name" should say "Waldino"
      And ".phone_number .data_display-value" should be empty
      And ".alternate_phone_number .data_display-value" should be empty
      And "email" should say "waldo@odlaw.org"
      And "dob" should say "2/28/1972"
      And "contact_preferences" should say "Email"
