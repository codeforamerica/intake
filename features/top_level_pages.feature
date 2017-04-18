Feature: HomePage Loads
  Scenario:
    Given that "/" loads
     Then it should have the "apply-now" link and say "Apply now"
      And it should have the "learn-more" link and say "Learn more"
      And "learn-more" should deeplink to "learn_more_section"
      And "apply-now" should link to "apply/"

Feature: Successful Application
  Scenario:
    Given that "apply/" loads
     When checkbox option "contracosta" is clicked
      And checkbox option "confirm_county_selection" is clicked
      And submit button is clicked
     Then it should load "application/"
      And it should say "You are applying for help in Contra Costa County."
     # you should see the counties that you are applying to
     # you should be able input a set of answers
      #   'contact_preferences' (multi checkbox) 'prefers_email',
      #   'first_name': "",
      #   'last_name': "",,
      #   'phone_number': "",
      #   'email': 'bgolder+testing@codeforamerica.org',
      #   'dob.day': str(random.randint(1, 31)),
      #   'dob.month': str(random.randint(1, 12)),
      #   'dob.year': str(random.randint(1959, 2000)),
      #   'us_citizen': radio options yes/no "yes" or "no",
      #   'address.street': self.generator.street_address(),
      #   'address.city': self.generator.city(),
      #   'address.state': self.generator.state_abbr(),
      #   'address.zip': self.generator.zipcode(),
      #   'on_probation_parole': radio options yes/no "yes" or "no",
      #   'serving_sentence': radio options yes/no "yes" or "no",
      #   'currently_employed': radio options yes/no "yes" or "no",
      #   'monthly_income': str(random.randint(100, 7000)),
      #   'monthly_expenses': str(random.randint(100, 3000)),
      #   'income_source': text field 'a job',
      #   'consent_to_represent': 'yes',
      #   'understands_limits': 'yes',
      #   'how_did_you_hear': text '',
      #   'additional_information': text '',
     }
     # 
