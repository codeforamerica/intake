Feature: An org user can search for an application and navigate to its detail page
	As on org user, I want to quickly search for an application
	in order to check the case status 

	Background:
	   Given an org user at "ebclc"
	     And "100" applications to "ebclc"
	     And a "ebclc" application to search for

	Scenario: Org user can search for application and find details
	 Given I log in as an org user at "ebclc"
		 And that "/applications/" loads
		When I search for the applicant's name
		Then I should see the applicant's name in search results
		When I click on the applicant's search result
		Then it should load the applicant's detail page
