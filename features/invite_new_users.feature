Feature: A staff user can invite a new user and they can accept it and sign up.
	As CfA staff, I want to invite new org users to the platform.

	Background:
	   Given a staff user
      And a "receiving-org" organization

	Scenario: CfA user can invite a new org user
	 Given I log in as a staff user
		 And that "/invitations/send-invite/" loads
		When I submit an invite to "attorney@law.org" at "receiving-org"
    Then "attorney@law.org" should receive an invite link
    When "attorney@law.org" follows the invite link
    Then it should load "/accounts/signup"