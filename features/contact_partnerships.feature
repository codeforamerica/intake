Feature: Visitor can submit a partnerships interest form
  Scenario: Visitor submits a minimal partnerships interest form
    Given that "/partnerships/get-in-touch" loads
     When the "name" text input is set to "Ziggy Stardust"
      And the "email" email input is set to "ziggy@mars.space"
      And the "organization_name" text input is set to "Spiders from Mars"
      And submit button in form "partnerships-contact-form" is clicked
     Then it should load "/partnerships/"
      And it should have the element ".flash.success" which says "Thanks for reaching out! Your message has been sent"