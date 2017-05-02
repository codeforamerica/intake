Feature: HomePage Loads and has Action Items
  Scenario: User clicks apply and learn more
    Given that "/" loads
     Then it should have the "apply-now" link and say "Apply now"
      And it should load css
      And it should have the "learn-more" link and say "Learn more"
      And "learn-more" should deeplink to "learn_more_section"
      And "apply-now" should link to "apply/"

