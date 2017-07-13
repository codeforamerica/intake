Feature: HomePage Loads and has Action Items
  Scenario: User clicks apply and learn more
    Given that "/" loads
     Then it should have the "apply-now" link and say "Start now"
      And it should load css
      And "apply-now" should link to "/apply/"

