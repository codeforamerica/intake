from .template_option import TemplateOption, TemplateOptionManager

# all of these are defined in the `template_options.json` fixture
CANT_PROCEED = 1
NO_CONVICTIONS = 2
NOT_ELIGIBLE = 3
ELIGIBLE = 4
COURT_DATE = 5
OUTCOME_GRANTED = 6
OUTCOME_DENIED = 7
TRANSFERRED = 8


class StatusType(TemplateOption):
    objects = TemplateOptionManager()
