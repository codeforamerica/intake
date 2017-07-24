Feature: Org users can print unread apps
  As an org user, I want to be able to easily print out unread applications
  so that I can keep track of all the incoming cases.

  Background: 
    Given a fillable PDF for "sf_pubdef"
     And "Bartholomew Simpson" applies to "San Francisco and Contra Costa"
     And "Inigo Montoya" applies to "San Francisco and Contra Costa"
     And an org user at "sf_pubdef"
     And an org user at "cc_pubdef"

  Scenario: SF looks at prebuilt PDF
    When I log in as an org user at "sf_pubdef"
     And I open "/applications/unread/"
    Then it should load "/applications/unread/"
     And I should see "2" in the active tab
     And there should be a pre-filled PDF for "Bartholomew Simpson"
     And there should be a pre-filled PDF for "Inigo Montoya"
     And there should be a prebuilt PDF bundle for "Bartholomew Simpson and Inigo Montoya" to "sf_pubdef"
    When I click the "Print All" link to "/applications/unread/pdf/"
    Then it should load "/applications/unread/pdf/"
     And I should see a flash message that says "2 applications have been marked as “Read” and moved to the “Needs Status Update” folder"
     And the main heading should say "2 applications to the San Francisco Public Defender"
     And it should have an iframe with "/applications/unread/pdf/prebuilt"

  Scenario: CoCo looks at PDF printout
    When I log in as an org user at "cc_pubdef"
     And I open "/applications/unread/"
    Then it should load "/applications/unread/"
     And I should see "2" in the active tab
    When I click the "Print All" link to "/applications/unread/pdf/"
    Then it should load "/applications/unread/pdf/"
     And I should see a flash message that says "2 applications have been marked as “Read” and moved to the “Needs Status Update” folder"
     And the main heading should say "2 applications to the Contra Costa Public Defender"
     And it should have an iframe with "/applications/unread/pdf/printout"
    When I open "/applications/unread/"
    Then it should load "/applications/unread/"
     And I should see "0" in the active tab
     And I should see "0" applications in the table when that tab is active
     And I should not see the Print All button
