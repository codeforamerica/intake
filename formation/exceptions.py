

class RawDataMustBeDictError(Exception):
    """Raise this if the input raw data for
    forms or form fields is not a dict or dict descendant
    (MultiValueDict, QueryDict)
    """
    pass


class NoChoicesGivenError(Exception):
    """Raise this when a field that operates on a set of
    choices is instantiated without any choices.
    """
    pass


class MultiValueFieldSubfieldError(NotImplementedError):
    """Raise this when someone tries to instantiate a
    MultiValueField without a defined `subfields` attribute
    """
    pass


class InvalidPhoneNumberException(Exception):
    """Raise this when an invalid phone number is found
    """
    pass
