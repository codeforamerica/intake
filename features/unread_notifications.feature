Feature: An org user can follow a notification to see unreads
    As an org user, I want to be able to receive a daily email with counts and
    a link to unread applications, so I don't miss any applications

    Background:
       Given an org user at "cc_pubdef"
         And "6" "read and updated" applications to "cc_pubdef"
         And "3" "needs update" applications to "cc_pubdef"
         And a "cc_pubdef" application to search for

    Scenario: Org user can follow an unreads link from an email
        Given I log in as an org user at "cc_pubdef"
          And it is a weekday
         Then org user at "cc_pubdef" should receive the unreads email
          And I should see "one unread application" in the email
          And I should see "4 applications awaiting a status update" in the email
          And I should see "all 10 applications" in the email
         When I click the unreads link in the email
         Then it should load "/applications/unread"
          And I should see "1" in the active tab
         When I click on the applicant's row
         Then it should load the applicant's detail page
         When I hit the browser back button
         Then I should see "0" in the active tab
          And I should not see the applicant listed