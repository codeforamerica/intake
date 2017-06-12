from behave import when


@when('applicant fills out a county application form with basic answers')
def step_impl(context):
    context.execute_steps('''
      When the "contact_preferences" checkbox option "prefers_email" is clicked
       And the "first_name" text input is set to "Jane"
       And the "last_name" text input is set to "Doe"
       And the "phone_number" text input is set to "5105555555"
       And the "email" text input is set to "testing@codeforamerica.org"
       And the "dob.day" text input is set to "1"
       And the "dob.month" text input is set to "1"
       And the "dob.year" text input is set to "1980"
       And "yes" is clicked on the "us_citizen" radio button
       And the "address.street" text input is set to "111 Coaster HWY"
       And the "address.city" text input is set to "San Francisco"
       And the "address.state" text input is set to "CA"
       And the "address.zip" text input is set to "91011"
       And "yes" is clicked on the "on_probation_parole" radio button
       And "yes" is clicked on the "serving_sentence" radio button
       And "yes" is clicked on the "currently_employed" radio button
       And the "monthly_income" text input is set to "1000"
       And the "monthly_expenses" text input is set to "1000"
       And "yes" is clicked on the "consent_to_represent" radio button
       And "yes" is clicked on the "understands_limits" radio button
       And the "how_did_you_hear" text input is set to "Listening"
       And the "additional_information" text input is set to "So cool"
    ''')
