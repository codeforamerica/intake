
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
