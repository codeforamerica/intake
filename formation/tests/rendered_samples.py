
NAMEFIELD = """<div class="field name">
  <label class="field-wrapping_label">
    <span class="field-display_text">
      Name
    </span>
    <span class="field-help_text">
      What should we call you?
    </span>
    <input type="text" name="name" value="">
  </label>
</div>"""

FRUITSFIELD = """<div class="field fruit">
  <fieldset>
    <legend>
      Fruit
    </legend>
    <ul class="radio_options options_list">
      <li>
        <label class="field-option_label">
          <input type="radio" name="fruit" value="apples">
          <span class="option-display_text">
            Apples
          </span>
        </label>
      </li>
      <li>
        <label class="field-option_label">
          <input type="radio" name="fruit" value="oranges">
          <span class="option-display_text">
            Oranges
          </span>
        </label>
      </li>
    </ul>
  </fieldset>
</div>"""

MULTIPLEFRUITSFIELD = """<div class="field fruit">
  <fieldset>
    <legend>
      Fruit
    </legend>
    <ul class="checkbox_options options_list">
    <li>
      <label class="field-option_label">
        <input type="checkbox" name="fruit" value="apples">
        <span class="option-display_text">
          Apples
        </span>
      </label>
    </li>
    <li>
      <label class="field-option_label">
        <input type="checkbox" name="fruit" value="oranges">
        <span class="option-display_text">
          Oranges
        </span>
      </label>
    </li>
    </ul>
  </fieldset>
</div>"""

DATEOFBIRTHFIELD = """<div class="field field-multivalue_fieldset dob">
  <fieldset>
    <legend>What is your date of birth?
    </legend>
    <div class="field-help_text">
      For example: 4/28/1986
    </div>
    <div class="subfield-row">
      <div class="subfield dob_month">
        <label class="field-wrapping_label">
          <span class="field-display_text">
            Month
          </span>
          <input type="text" name="dob.month" value="">
        </label>
      </div>
      <div class="subfield dob_day">
        <label class="field-wrapping_label">
          <span class="field-display_text">
            Day
          </span>
          <input type="text" name="dob.day" value="">
        </label>
      </div>
      <div class="subfield dob_year">
        <label class="field-wrapping_label">
          <span class="field-display_text">
            Year
          </span>
          <input type="text" name="dob.year" value="">
        </label>
      </div>
    </div>
  </fieldset>
</div>"""

FORM_DISPLAY = """
<div class="data_display datum contact_preferences">
  <div class="data_display-label">Contact preferences</div>
  <div class="data_display-value">Text Message</div>
</div>
<div class="data_display datum first_name">
  <div class="data_display-label">First name</div>
  <div class="data_display-value">Wess</div>
</div>
<div class="data_display datum middle_name">
  <div class="data_display-label">Middle name</div>
  <div class="data_display-value">Gussie</div>
</div>
<div class="data_display datum last_name">
  <div class="data_display-label">Last name</div>
  <div class="data_display-value">Kutch</div>
</div>
<div class="data_display datum phone_number">
  <div class="data_display-label">Phone number</div>
  <div class="data_display-value">671-928-8799</div>
</div>
<div class="data_display datum email">
  <div class="data_display-label">Email</div>
  <div class="data_display-value">anson16@gmail.com</div>
</div>
<div class="data_display datum address">
  <div class="data_display-label">Address</div>
  <div class="data_display-value">
  <pre>973 Migdalia Plain
New Anwarville, AZ
62145</pre></div>
</div>
<div class="data_display datum dob">
  <div class="data_display-label">Date of birth</div>
  <div class="data_display-value">3/19/1999</div>
</div>
<div class="data_display datum ssn">
  <div class="data_display-label">SSN</div>
  <div class="data_display-value">214259752</div>
</div>
<div class="data_display datum us_citizen">
  <div class="data_display-label">Is a citizen</div>
  <div class="data_display-value">Yes</div>
</div>
<div class="data_display datum being_charged">
  <div class="data_display-label">Is currently being charged</div>
  <div class="data_display-value">No</div>
</div>
<div class="data_display datum serving_sentence">
  <div class="data_display-label">Is serving a sentence</div>
  <div class="data_display-value">No</div>
</div>
<div class="data_display datum on_probation_parole">
  <div class="data_display-label">Is on probation or parole</div>
  <div class="data_display-value">No</div>
</div>
<div class="data_display datum where_probation_or_parole">
  <div class="data_display-label">Probation/Parole location</div>
  <div class="data_display-value empty"></div>
</div>
<div class="data_display datum when_probation_or_parole">
  <div class="data_display-label">Probation/Parole ends</div>
  <div class="data_display-value empty"></div>
</div>
<div class="data_display datum rap_outside_sf">
  <div class="data_display-label">Has RAP outside SF</div>
  <div class="data_display-value">No</div>
</div>
<div class="data_display datum when_where_outside_sf">
  <div class="data_display-label">Convictions/arrests outside SF</div>
  <div class="data_display-value empty"></div>
</div>
<div class="data_display datum currently_employed">
  <div class="data_display-label">Is employed</div>
  <div class="data_display-value">Yes</div>
</div>
<div class="data_display datum monthly_income">
  <div class="data_display-label">Monthly income</div>
  <div class="data_display-value">6471</div>
</div>
<div class="data_display datum monthly_expenses">
  <div class="data_display-label">Monthly expenses</div>
  <div class="data_display-value">803</div>
</div>
<div class="data_display datum how_did_you_hear">
  <div class="data_display-label">Heard about this from</div>
  <div class="data_display-value empty"></div>
</div>"""
