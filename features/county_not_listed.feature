Feature: DEPRECATED: Applicants can apply for help in counties where we don't have partners
  As an applicant, I should be able to tell CMR when the county I need isn't
  listed, so that they can send me information about how to apply in all the
  places I need to clear my record.

  Scenario: CfA staff can view 'not-listed' apps
     Given an applicant support user
       And "5" applications to "cfa"
       And I log in as an applicant support user
       And that "/applications/county_not_listed" loads
      Then I should see "5" in the active tab
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
