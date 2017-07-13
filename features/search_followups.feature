Feature: A staff user can search for and modify submissions 
	As CfA staff, I want to quickly search for an applicant
	in order to add a note and provide case support for applicants.

	Background:
	   Given an applicant support user
	     And "100" applications
	     And an applicant to search for

	Scenario: CfA user can find applicant and add a note
	 Given I log in as an applicant support user
		 And that "/applications/" loads
		When I search for the applicant's name
		Then I should see the applicant's followup row
		 And the create note form should be visible
		When I add a note about the applicant's case
		Then the note should be visible
