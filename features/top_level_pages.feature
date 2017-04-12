Feature: HomePage Loads
  Scenario:
    Given that "/" loads
     Then it should have the "apply-now" link and say "Apply now"
      And it should have the "learn-more" link and say "Learn more"
      And "learn-more" should deeplink to "learn_more_section"
      And "apply-now" should link to "apply/"
