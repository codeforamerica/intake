Feature: Maintenance page loads when environment variable is set
  Background:
    Given that MAINTENANCE_MODE is true

  Scenario: User loads the root url when maintenance mode is true
    Given that "/" loads
    Then it should have the element ".maintenance-message" which says "Sorry, the page is down for maintenance at the moment."

