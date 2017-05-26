Feature: A staff user can search for and modify submissions 
	As CfA staff
	I want to quickly search for an applicant
	In order to add a note and provide case support for applicants

	Background:
		Given an applicant support user
		  And multiple pages of applicants
		  And an applicant

	Scenario: CfA user can find applicant and add a note
		Given I am logged in as an applicant support user
		 And I am on the "/applications/" page
		When I search for the applicant's name
		Then I should see the applicant's followup row
		 And the note input should be visible
		When I add a note about the applicant's case
		Then the note should be visible

