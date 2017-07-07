Feature: An org user can view applications to their organization
	As an org user, I want to be able to see all applications, including those that I have not yet read or created a status for

	Background:
	   Given an org user at "cc_pubdef"
	     And "6" "read and updated" applications to "cc_pubdef"
	     And "3" "needs update" applications to "cc_pubdef"
	     And "15" applications to "cc_pubdef"


	Scenario: Org user can see a list of all unread applications in the "Unread" tab
	 Given I log in as an org user at "cc_pubdef"
		 And that "/applications/unread" loads
		Then I should see "15" in the active tab
		 And I should see "15" applications in the table when that tab is active
		 And I should see the Print All button

	Scenario: Org user can see a list of all applications needing a status update in the "Needs Status Update" tab
	 Given I log in as an org user at "cc_pubdef"
		 And that "/applications/needs_update" loads
		Then I should see "18" in the active tab
		 And I should see "18" applications in the table when that tab is active
		 And I should not see the Print All button


	Scenario: Org user can see a list of all unread applications in the "All" tab
	 Given I log in as an org user at "cc_pubdef"
		 And that "/applications/all" loads
		Then I should see "24" in the active tab
		 And I should see "24" applications in the table when that tab is active
		 And I should not see the Print All button
