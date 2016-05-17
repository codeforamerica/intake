
def yesno(s, key=None):
    if not key:
        return 'Off'
    result = s.answers.get(key, '')
    if not result:
        return 'Off'
    if result in ('yes', 'no'):
        return result.capitalize()

def get_formatted_dob(s):
    return '{}/{}/{}'.format(
                s.answers.get('dob_month', ''),
                s.answers.get('dob_day', ''),
                s.answers.get('dob_year', ''))


def fmt_ssn(s, prefix='SS# '):
    ssn = s.answers.get('ssn', '')
    if ssn:
        digits = ''.join([d for d in ssn if d.isnumeric()])
        return '{}{}-{}-{}'.format(prefix, digits[:3], digits[3:5], digits[5:])
    return ''


def translator(s):
    return {
            'Address City': 'address_city',
            'Address State': 'address_state',
            'Address Street': 'address_street',
            'Address Zip': 'address_zip',
            'Arrested outside SF': lambda s: yesno(s, 'rap_outside_sf'),
            'Cell phone number': 'phone_number',
            'Charged with a crime': lambda s: yesno(s, 'being_charged'),
            'Date': lambda s: s.get_local_date_received('%-m/%-d/%Y'),
            'Date of Birth': get_formatted_dob,
            'Dates arrested outside SF': 'when_where_outside_sf',
            'Drivers License': 'drivers_license_number',
            'Email Address': 'email',
            'Employed': lambda s: yesno(s, 'currently_employed'),
            'First Name': 'first_name',
            'Home phone number': '',
            'How did you hear about the Clean Slate Program': 'how_did_you_hear',
            'If probation where and when?': lambda s: '{} {}'.format(
                s.answers.get('where_probation_or_parole'),
                s.answers.get('when_probation_or_parole')),
            'Last Name': 'last_name',
            'MI': lambda s: s.answers.get('middle_name', '')[:1],
            'May we leave voicemail': lambda s: yesno(s),
            'May we send mail here': lambda s: yesno(s),
            'Monthly expenses': 'monthly_expenses',
            'On probation or parole': lambda s: yesno(s, 'on_probation_parole'),
            'Other phone number': '',
            'Serving a sentence': lambda s: yesno(s, 'serving_sentence'),
            'Social Security Number': lambda s: fmt_ssn(s, ''),
            'US Citizen': lambda s: yesno(s, 'us_citizen'),
            'What is your monthly income': 'monthly_income',
            'Work phone number': '',
            'DOB': get_formatted_dob,
            'SSN': fmt_ssn,
            'FirstName': 'first_name',
            'LastName': 'last_name'
        }