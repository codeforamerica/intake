Feature: CRUD events are audited
  Background:
    Given a superuser
      And an org user at "ebclc"
  
  Scenario: Admin actions create CRUD events
    Given I log in as a superuser
     When I go to the admin edit page for "ebclc" user
      And I check "is_staff"
      And I select the "followup_staff" option in "groups_old"
      And I click "a#id_groups_add_link"
      And I click "input[name='_save']"
     Then the latest "auth.User" "update" event should have "superuser" as the user
      And the latest "auth.User" "update" event should have "True" for "is_staff"
      And the latest "auth.User" "m2m_change" event should have "2" ids in "groups"
