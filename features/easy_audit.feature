Feature: CRUD events are audited
  Background:
    Given an org user at "sf_pubdef"
      And a fillable PDF for "sf_pubdef"
  
  Scenario: Automated CRUD events don't use cached users
    Given I log in as an org user at "sf_pubdef"
     When "Bartholomew Simpson" applies to "San Francisco and Contra Costa"
     Then there should be a pre-filled PDF for "Bartholomew Simpson"
     Then the latest CRUD event should not have a user
