Feature: DEPRECATED: Applicants can apply for help in counties where we don't have partners
  As an applicant, I should be able to tell CMR when the county I need isn't
  listed, so that they can send me information about how to apply in all the
  places I need to clear my record.

  # DEPRECATED
  # Scenario: Applicant can apply for two counties that aren't listed
  #   Given that "/apply/" loads
  #    When the "counties" checkbox option "not_listed" is clicked
  #     And submit button in form "county_form" is clicked
  #    Then it should load "/application/"
  #     And "application_county_list" should say "You are applying for help in counties where we don't have official partners"
  #    When applicant fills out county not listed form fields
  #     And the "unlisted_counties" text input is set to "Delta Quadrant, Narnia County"
  #     And submit button in form "county_form" is clicked
  #    Then it should load "/review/"
  #    When I click "button.action-forward"
  #    Then it should load "/thanks/"
  #     And "next_steps" should say "We will contact you in the next week with information on how to clear your record in Delta Quadrant, Narnia County"

  # # DEPRECATED 
  # Scenario: Applicant can apply for an unlisted county along with a listed one
  #   Given that "/apply/" loads
  #    When the "counties" checkbox option "not_listed" is clicked
  #     And the "counties" checkbox option "contracosta" is clicked
  #     And submit button in form "county_form" is clicked
  #    Then it should load "/application/"
  #     And "application_county_list" should say "You are applying for help in Contra Costa and counties where we don't have official partners."
  #    When applicant fills out a county application form with basic answers
  #     And applicant fills out additional fields for Contra Costa
  #     And the "unlisted_counties" text input is set to "Delta Quadrant, Narnia County"
  #     And submit button in form "county_form" is clicked
  #    Then it should load "/review/"
  #    When I click "button.action-forward"
  #    Then it should load "/thanks/"
  #     And "next_steps" should say "We will contact you in the next week with information on how to clear your record in Delta Quadrant, Narnia County"

  Scenario: CfA staff gets reminders and can view 'not-listed' apps
     Given an applicant support user
       And "5" applications to "cfa"
       And I log in as an applicant support user
       And it is a weekday
      Then the app should send a slack notification about new CNL apps
      When I click on the link in the slack message about new CNL apps
      Then it should load "/applications/county_not_listed"
       And I should see "5" in the active tab
      When I add a note on the first application that says
        """
        Contacted the applicant with information about the county
        """
       And I add a "CNL - Complete" tag on the first application
      Then the notes on the first application should include
        """
        Contacted the applicant with information about the county
        """
       And the tags on the first application should include "CNL - Complete"
