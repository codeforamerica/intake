from intake.translators.base import AttributeTranslatorBase


translate = AttributeTranslatorBase({
        'Given Name Text Box': lambda s: s['first_name'].capitalize(),
        'Family Name Text Box': 'last_name',
        'Address 1 Text Box': 'address_street',
        'Postcode Text Box': 'address_zip',
        'City Text Box': 'address_city'
    })