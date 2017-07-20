import io
import string
import collections

from django.conf import settings
from reportlab.pdfgen.canvas import Canvas

from reportlab.lib.pagesizes import letter
from reportlab.lib import units, colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph


digit_chars = string.digits + '.'
unit_lookup = {
    'pt': 1,
    'in': units.inch,
    'cm': units.cm,
    'mm': units.mm
}

Margin = collections.namedtuple("Margin", ['top', 'right', 'bottom', 'left'])
Size = collections.namedtuple("Size", ['x', 'y', 'width', 'height'])
Position = collections.namedtuple("Position", ['x', 'y'])
LEADING_FACTOR = 1.2


def Style(name, font='Helvetica', size=12, leading=None, color=colors.black):
    return ParagraphStyle(
        name,
        fontName=font,
        fontSize=size,
        leading=leading or size * LEADING_FACTOR,
        textColor=color
    )


LABEL_STYLE = Style('label', 'Helvetica', size=10, color=colors.gray)
BODY_STYLE = Style('body', 'Times')
VALUE_STYLE = Style('value', 'Helvetica')
FOOTNOTE_STYLE = Style('footnote', 'Courier', size=9)


def u(amount):
    units = ''.join([c for c in amount if c in string.ascii_letters])
    units = units.lower()
    number_string = ''.join([c for c in amount if c in digit_chars])
    if '.' in number_string:
        number = float(number_string)
    else:
        number = int(number_string)
    multiplier = unit_lookup.get(units, 1)
    return number * multiplier


class PDFFormDisplay:

    main_display_fields = [
        ['date_received', 'counties'],
        ['first_name', 'middle_name', 'last_name'],
        ['aliases'],
        ['dob', 'last_four', 'driver_license_or_id', 'ssn', 'case_number',
         'pfn_number'],
        ['preferred_pronouns'],
        ['contact_preferences'],
        ['phone_number', 'alternate_phone_number'],
        ['email'],
        ['address'],
        ['is_california_resident', 'how_long_california_resident'],
        ['currently_employed', 'income_source'],
        ['monthly_income', 'monthly_expenses'],
        ['household_size', 'dependents', 'has_children', 'is_married'],
        ['owns_home', 'on_public_benefits'],
        ['how_did_you_hear'],
        [
            'understands_limits',
            'consent_to_represent'
        ],
        [
            'identity_confirmation',
            'understands_maybe_fee'
        ],
        ['additional_information'],
    ]

    case_status_fields = [
        ['us_citizen'],
        ['is_veteran'],
        ['is_student'],
        [
            'on_probation_parole',
            'where_probation_or_parole',
            'when_probation_or_parole',
            'finished_half_probation',
            'reduced_probation',
        ],
        ['being_charged'],
        ['serving_sentence'],
        [
            'rap_outside_sf',
            'when_where_outside_sf'
        ],
        ['has_suspended_license'],
        ['owes_court_fees'],
        ['reasons_for_applying'],
    ]

    letter_display_fields = [
        'declaration_letter_intro',
        'declaration_letter_life_changes',
        'declaration_letter_activities',
        'declaration_letter_goals',
        'declaration_letter_why',
    ]

    field_bottom_margin = 14
    related_field_bottom_margin = 4

    def __init__(self, display_form, letter_display=None, canvas=None):
        self.file = io.BytesIO()
        self.width, self.height = letter
        self.canvas = canvas
        if not canvas:
            self.canvas = Canvas(
                self.file,
                pagesize=letter)
            self.canvas.setAuthor('Clear My Record, Code for America')
        self.frame = Margin(
            u('1in'),
            u('.75in'),
            u('1in'),
            u('.75in'))
        self.form = display_form
        self.letter = letter_display
        self.cursor = Position(
            self.frame.left,
            self.height - self.frame.top
        )
        self.nice_date = \
            self.form.date_received.get_current_value().strftime("%B %-d, %Y")

    def set_cursor(self, x, y):
        self.cursor = Position(x, y)
        return self.cursor

    def move_cursor(self, x=0, y=0):
        return self.set_cursor(
            self.cursor.x + x,
            self.cursor.y + y)

    def draw_paragraph(self, text, max_width, max_height, style):
        if not text:
            text = ''
        if not isinstance(text, str):
            text = str(text)
        text = text.strip(string.whitespace)
        text = text.replace('\n', "<br/>")
        p = Paragraph(text, style)
        used_width, used_height = p.wrap(max_width, max_height)
        line_widths = p.getActualLineWidths0()
        number_of_lines = len(line_widths)
        if number_of_lines > 1:
            actual_width = used_width
        elif number_of_lines == 1:
            actual_width = min(line_widths)
            used_width, used_height = p.wrap(actual_width + 0.1, max_height)
        else:
            return 0, 0
        p.drawOn(self.canvas, self.cursor.x, self.cursor.y - used_height)
        return used_width, used_height

    def draw_field_label(self, text, max_width):
        return self.draw_paragraph(
            text,
            max_width,
            LABEL_STYLE.leading * 2,
            LABEL_STYLE)

    def draw_field_value(self, text, max_width):
        return self.draw_paragraph(
            text,
            max_width,
            u('5in'),
            VALUE_STYLE)

    def draw_field(self, field, max_width):
        label_text = field.get_display_label()
        label_width, label_height = \
            self.draw_field_label(label_text, max_width)
        self.move_cursor(0, -label_height)
        value_width, value_height = self.draw_field_value(
            field.get_display_value(), max_width)
        total_width = max([label_width, value_width])
        total_height = label_height + value_height
        return total_width, total_height

    def keys_to_fields(self, keys, form_attr='form'):
        form = getattr(self, form_attr)
        return [
            form.fields[key]
            for key in keys
            if key in form.fields]

    def draw_vertical_section(self, fields, max_width):
        existing_fields = self.keys_to_fields(fields)
        if not existing_fields:
            return (0, 0)
        heights = []
        widths = []
        for field_index, field in enumerate(existing_fields):
            if field_index > 0:
                self.move_cursor(0, -self.related_field_bottom_margin)
                heights.append(self.related_field_bottom_margin)
            label_text = field.get_display_label()
            dx, dy = self.draw_field_label(label_text, max_width)
            self.move_cursor(0, -dy)
            heights.append(dy)
            widths.append(dx)
            value_text = field.get_display_value()
            dx, dy = self.draw_field_value(value_text, max_width)
            widths.append(dx)
            self.move_cursor(0, -dy)
            heights.append(dy)
        return max(widths), sum(heights)

    def draw_field_row(self, fields, max_width):
        self.cursor = Position(self.frame.left, self.cursor.y)
        field_index = 0
        field_gutter = 24
        existing_fields = self.keys_to_fields(fields)
        num_fields = len(existing_fields)
        if not num_fields:
            return (0, 0)
        num_gutters = num_fields - 1
        max_row_width = max_width
        total_gutter_width = field_gutter * num_gutters
        max_field_width = \
            (max_row_width - total_gutter_width) / num_fields
        field_heights = []
        incremental_widths = []
        for field in existing_fields:
            if field_index > 0:
                self.move_cursor(field_gutter, 0)
                incremental_widths.append(field_gutter)
            start_point = self.cursor
            dx, dy = self.draw_field(field, max_field_width)
            incremental_widths.append(dx)
            field_heights.append(dy)
            self.set_cursor(start_point.x + dx, start_point.y)
            field_index += 1
        return (
            sum(incremental_widths),
            max(field_heights)
        )

    def draw_main_fields(self):
        self.set_cursor(self.frame.left, self.height - self.frame.top)
        max_width = u('4.75in')
        for row in self.main_display_fields:
            start = self.cursor
            dx, dy = self.draw_field_row(row, max_width)
            margin = self.field_bottom_margin if dx else 0
            self.set_cursor(
                self.frame.left,
                start.y - (dy + margin))

    def draw_case_status_fields(self):
        left_edge = u('5.625in')
        max_width = u('2.125in')
        self.set_cursor(left_edge, self.height - self.frame.top)
        for section in self.case_status_fields:
            dx, dy = self.draw_vertical_section(section, max_width)
            vertical_margin = self.field_bottom_margin if dx else 0
            self.move_cursor(0, -vertical_margin)

    def draw_letter(self):
        max_width = u('6.5in')
        max_height = self.height - (
            self.frame.top + self.frame.bottom)
        self.set_cursor(u('1in'), self.height - self.frame.top)
        dx, dy = self.draw_paragraph(
            self.nice_date, max_width, max_height, BODY_STYLE)
        self.move_cursor(0, -(dy + self.field_bottom_margin))
        dx, dy = self.draw_paragraph(
            "To Whom It May Concern,", max_width, max_height, BODY_STYLE)
        self.move_cursor(0, -(dy + self.field_bottom_margin))
        for field in self.keys_to_fields(self.letter_display_fields, 'letter'):
            dx, dy = self.draw_paragraph(
                field.get_display_value(), max_width, max_height, BODY_STYLE)
            self.move_cursor(0, -(dy + self.field_bottom_margin))
        dx, dy = self.draw_paragraph(
            "Sincerely,", max_width, max_height, BODY_STYLE)
        self.move_cursor(0, -(dy + self.field_bottom_margin))
        full_name = " ".join([
            self.form.first_name.get_display_value(),
            self.form.last_name.get_display_value()
        ])
        dx, dy = self.draw_paragraph(
            full_name, max_width, max_height, BODY_STYLE)

    def draw_header(self):
        self.set_cursor(self.frame.left, self.height - u('0.5in'))
        width = self.width - u('1.5in')
        dx, dy = self.draw_paragraph(
            self.form.submission.get_external_url(),
            width, u('0.5in'),
            FOOTNOTE_STYLE
        )

    def render(self, save=True, title=None):
        self.draw_header()
        self.draw_main_fields()
        self.draw_case_status_fields()
        self.canvas.showPage()
        if self.letter:
            self.draw_letter()
            self.canvas.showPage()
        if title:
            self.canvas.setTitle(title)
        if save:
            self.canvas.save()
        return self.canvas, self.file
