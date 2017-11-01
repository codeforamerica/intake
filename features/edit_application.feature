Feature: An org user can edit some application data for applications to their organization

  Background:
    Given an org user at "fresno_pubdef"

  Scenario: Org user can edit allowed details for application and save
    Given I log in as an org user at "fresno_pubdef"
      And a "fresno_pubdef" application to search for
      And I open the applicant's detail page
     When I click the "Edit info" link to the applicant's edit page
     Then it should load the applicant's edit page
      And it should not show the "ssn" field
      And it should not show the "being_charged" field
      And it should not show the "additional_information" field
     When the "last_name" text input is set to "Waldino"
      And the "phone_number" text input is set to "4152124848"
      And the "alternate_phone_number" text input is set to "4152124848"
      And the "email" text input is set to "waldo@odlaw.org"
      And the "driver_license_or_id" text input is set to "D82774356"
      And the "aliases" text input is set to "Wally"
      And the "dob.month" text input is set to "10"
      And the "dob.day" text input is set to "28"
      And the "dob.year" text input is set to "1950"
      And the "address.street" text input is set to "111 Unfindable Circle"
      And the "address.city" text input is set to "Oakland"
      And the "address.state" text input is set to "California"
      And the "address.zip" text input is set to "94609"
      And the "contact_preferences" checkbox option "prefers_sms" is clicked
      And submit button in form "application_edit_form" is clicked
     Then it should load the applicant's detail page
      And "last_name" should say "Waldino"
      And "phone_number" should say "(415) 212-4848"
      And "alternate_phone_number" should say "(415) 212-4848"
      And "email" should say "waldo@odlaw.org"
      And "driver_license_or_id" should say "D82774356"
      And "aliases" should say "Wally"
      And "dob" should say "10/28/1950"
      And "address" should say "111 Unfindable Circle"
      And "address" should say "Oakland"
      And "address" should say "California"
      And "address" should say "94609"
      And "contact_preferences" should say "Email"
