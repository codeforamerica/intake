Feature: SF gets premade PDFs
  As an SF org user, I want to have prebuilt PDF forms
  so that I can quickly print new submissions

  Background:
    Given a fillable PDF for "sf_pubdef"

  Scenario: Application for SF prebuilds PDFs
     When "Bartholomew Simpson" applies to "San Francisco and Contra Costa"
     Then there should be a pre-filled PDF for "Bartholomew Simpson"
      And "Bartholomew Simpson" should be in the new apps PDF for "sf_pubdef"
      And there should not be a new apps PDF for "cc_pubdef"