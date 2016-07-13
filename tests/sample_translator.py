from intake.translators.base import FormToPDFTranslator


translate = FormToPDFTranslator({
        'Given Name Text Box': lambda s: s.answers['first_name'].capitalize(),
        'Family Name Text Box': 'last_name',
        'Address 1 Text Box': 'address_street',
        'Postcode Text Box': 'address_zip',
        'City Text Box': 'address_city'
    }, att_object_extractor='answers')